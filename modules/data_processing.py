import pandas as pd
import numpy as np

def process_data(df, selected_samples, am_dict, ignore_am):
    df_filtered = df[df['Name'].isin(selected_samples)].copy()
    elements = ['N', 'C', 'H', 'S']
    available_elements = [el for el in elements if el in df_filtered.columns]
    
    grouped = df_filtered.groupby('Name', sort=False)[available_elements].agg(['mean', 'std']).reset_index()
    grouped.columns = ['Name'] + [f"{el}_{stat}" for el in available_elements for stat in ['mean', 'std']]
    
    grouped['__sort_key__'] = pd.Categorical(grouped['Name'], categories=selected_samples, ordered=True)
    grouped = grouped.sort_values('__sort_key__').drop(columns=['__sort_key__']).reset_index(drop=True)
    
    for el in available_elements:
        if f"{el}_std" in grouped.columns:
            grouped[f"{el}_std"] = grouped[f"{el}_std"].fillna(0)
        if f"{el}_mean" in grouped.columns:
            grouped[f"{el}_mean"] = grouped[f"{el}_mean"].fillna(0)

    # Calcoli O e Parametri Avanzati
    o_means, o_stds = [], []
    hhv_means, nc_means, hc_means, oc_means = [], [], [], []
    
    for _, row in grouped.iterrows():
        name = row['Name']
        c = row.get('C_mean', 0.0)
        h = row.get('H_mean', 0.0)
        n = row.get('N_mean', 0.0)
        s = row.get('S_mean', 0.0)
        
        sum_chns = c + h + n + s
        var_sum = sum(row.get(f'{el}_std', 0.0)**2 for el in available_elements)
        sd_o = np.sqrt(var_sum)
        
        if ignore_am:
            o_val = 100 - sum_chns
        else:
            umidita = am_dict.get(name, {}).get('Umidità', 0.0) or 0.0
            ceneri = am_dict.get(name, {}).get('Ceneri', 0.0) or 0.0
            o_val = 100 - sum_chns - umidita - ceneri
            
        o_val = max(0, o_val)
        o_means.append(o_val)
        o_stds.append(sd_o)
        
        # Calcolo Parametri per Plotly
        hhv = 0.3491*c + 1.1783*h + 0.1005*s - 0.1034*o_val - 0.0151*n
        hhv_means.append(max(0, hhv)) # HHV non può essere negativo
        
        nc_means.append((n/14.007)/(c/12.011) if c > 0 else 0)
        hc_means.append((h/1.008)/(c/12.011) if c > 0 else 0)
        oc_means.append((o_val/16)/(c/12.011) if c > 0 else 0)

    grouped['O_mean'] = o_means
    grouped['O_std'] = o_stds
    grouped['HHV_mean'] = hhv_means
    grouped['NC_mean'] = nc_means
    grouped['HC_mean'] = hc_means
    grouped['OC_mean'] = oc_means

    # Aggiunta Moisture e Ash
    moisture_means, ash_means = [], []
    for nm in grouped['Name']:
        if not ignore_am:
            moisture_means.append(am_dict.get(nm, {}).get('Umidità', 0.0) or 0.0)
            ash_means.append(am_dict.get(nm, {}).get('Ceneri', 0.0) or 0.0)
        else:
            moisture_means.append(0.0)
            ash_means.append(0.0)

    grouped['Moisture_mean'] = moisture_means
    grouped['Ash_mean'] = ash_means

    # Creazione Foglio 2
    cols_means = ['Name'] + [f"{el}_mean" for el in available_elements] + ['O_mean']
    means_only_df = grouped[cols_means].copy()
    rename_dict = {f"{el}_mean": f"{el} (%)" for el in available_elements}
    rename_dict['O_mean'] = 'O (%)'
    means_only_df = means_only_df.rename(columns=rename_dict)
    
    if not ignore_am:
        means_only_df['Moisture (%)'] = [am_dict.get(nm, {}).get('Umidità', 0.0) or 0.0 for nm in grouped['Name']]
        means_only_df['Ash (%)'] = [am_dict.get(nm, {}).get('Ceneri', 0.0) or 0.0 for nm in grouped['Name']]

    # Creazione Foglio 3
    pretty_df = pd.DataFrame()
    pretty_df['Name'] = grouped['Name']
    
    for el in available_elements:
        pretty_df[f"{el} (%)"] = grouped.apply(lambda x: f"{x.get(el+'_mean', 0.0):.2f} ± {x.get(el+'_std', 0.0):.2f}", axis=1)
        
    pretty_df["O (%)"] = grouped.apply(lambda x: f"{x.get('O_mean', 0.0):.2f} ± {x.get('O_std', 0.0):.2f}", axis=1)
        
    if not ignore_am:
        pretty_df['Moisture (%)'] = [f"{(am_dict.get(nm, {}).get('Umidità', 0.0) or 0.0):.2f}" for nm in grouped['Name']]
        pretty_df['Ash (%)'] = [f"{(am_dict.get(nm, {}).get('Ceneri', 0.0) or 0.0):.2f}" for nm in grouped['Name']]

    return grouped, pretty_df, means_only_df
