import pandas as pd
import numpy as np

def process_data(df, selected_samples, am_dict, ignore_am):
    """
    Filtra, raggruppa e calcola Media, SD e O.
    Rispetta rigorosamente l'ordine personalizzato imposto dall'utente.
    """
    # Filtro sample
    df_filtered = df[df['Name'].isin(selected_samples)].copy()
    
    elements = ['N', 'C', 'H', 'S']
    available_elements = [el for el in elements if el in df_filtered.columns]
    
    # Raggruppa. sort=False evita che Pandas li metta in automatico in ordine alfabetico
    grouped = df_filtered.groupby('Name', sort=False)[available_elements].agg(['mean', 'std']).reset_index()
    
    # Appiattiamo il MultiIndex
    grouped.columns = ['Name'] + [f"{el}_{stat}" for el in available_elements for stat in ['mean', 'std']]
    
    # FIX CRUCIALE: Forziamo il dataframe calcolato a seguire ESATTAMENTE l'ordine della tua lista
    grouped['__sort_key__'] = pd.Categorical(grouped['Name'], categories=selected_samples, ordered=True)
    grouped = grouped.sort_values('__sort_key__').drop(columns=['__sort_key__']).reset_index(drop=True)
    
    # Riempi NaN nella Dev Standard con 0
    for el in available_elements:
        if f"{el}_std" in grouped.columns:
            grouped[f"{el}_std"] = grouped[f"{el}_std"].fillna(0)
        if f"{el}_mean" in grouped.columns:
            grouped[f"{el}_mean"] = grouped[f"{el}_mean"].fillna(0)

    # --- Calcolo Ossigeno (O) ---
    o_means = []
    o_stds = []
    
    for _, row in grouped.iterrows():
        name = row['Name']
        
        sum_chns = sum(row.get(f'{el}_mean', 0.0) for el in available_elements)
        var_sum = sum(row.get(f'{el}_std', 0.0)**2 for el in available_elements)
        sd_o = np.sqrt(var_sum)
        
        if ignore_am:
            o_val = 100 - sum_chns
        else:
            umidita = am_dict.get(name, {}).get('Umidità', 0.0) or 0.0
            ceneri = am_dict.get(name, {}).get('Ceneri', 0.0) or 0.0
            o_val = 100 - sum_chns - umidita - ceneri
            
        o_means.append(max(0, o_val))
        o_stds.append(sd_o)
        
    grouped['O_mean'] = o_means
    grouped['O_std'] = o_stds
    
    # Aggiungiamo Moisture e Ash al dataframe 'grouped' per renderli disponibili nei grafici
    moisture_means = []
    ash_means = []
    for n in grouped['Name']:
        if not ignore_am:
            moisture_means.append(am_dict.get(n, {}).get('Umidità', 0.0) or 0.0)
            ash_means.append(am_dict.get(n, {}).get('Ceneri', 0.0) or 0.0)
        else:
            moisture_means.append(0.0)
            ash_means.append(0.0)

    grouped['Moisture_mean'] = moisture_means
    grouped['Moisture_std'] = 0.0  # Input utente singolo, no deviazione standard
    grouped['Ash_mean'] = ash_means
    grouped['Ash_std'] = 0.0

    # --- Creazione Foglio 2 (Solo Medie) ---
    cols_means = ['Name'] + [f"{el}_mean" for el in available_elements] + ['O_mean']
    means_only_df = grouped[cols_means].copy()
    
    rename_dict = {f"{el}_mean": f"{el} (%)" for el in available_elements}
    rename_dict['O_mean'] = 'O (%)'
    means_only_df = means_only_df.rename(columns=rename_dict)
    
    if not ignore_am:
        means_only_df['Moisture (%)'] = [am_dict.get(n, {}).get('Umidità', 0.0) or 0.0 for n in grouped['Name']]
        means_only_df['Ash (%)'] = [am_dict.get(n, {}).get('Ceneri', 0.0) or 0.0 for n in grouped['Name']]

    # --- Creazione Foglio 3 (Pretty / Formattato) ---
    pretty_df = pd.DataFrame()
    pretty_df['Name'] = grouped['Name']
    
    for el in available_elements:
        pretty_df[f"{el} (%)"] = grouped.apply(
            lambda x: f"{x.get(el+'_mean', 0.0):.2f} ± {x.get(el+'_std', 0.0):.2f}", axis=1
        )
        
    # Colonna O nel foglio formattato
    pretty_df["O (%)"] = grouped.apply(
        lambda x: f"{x.get('O_mean', 0.0):.2f} ± {x.get('O_std', 0.0):.2f}", axis=1
    )
        
    if not ignore_am:
        pretty_df['Moisture (%)'] = [f"{(am_dict.get(n, {}).get('Umidità', 0.0) or 0.0):.2f}" for n in grouped['Name']]
        pretty_df['Ash (%)'] = [f"{(am_dict.get(n, {}).get('Ceneri', 0.0) or 0.0):.2f}" for n in grouped['Name']]

    return grouped, pretty_df, means_only_df
