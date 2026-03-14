import pandas as pd
import numpy as np

def process_data(df, selected_samples, am_dict, ignore_am):
    """
    Filtra, raggruppa e calcola Media, SD e O2.
    Restituisce 3 DataFrame: 
    1. stats_df (Dati completi per i grafici)
    2. pretty_df (Tabella estetica per Excel Foglio 3)
    3. means_only_df (Tabella per Excel Foglio 2)
    """
    # Filtro sample
    df_filtered = df[df['Name'].isin(selected_samples)].copy()
    
    # Raggruppa e calcola
    elements = ['N', 'C', 'H', 'S']
    
    # Assicurati che le colonne esistano e converti i NaN (es: i trattini) in 0 o drop
    # Per il calcolo consideriamo dropna intrinseco in groupby.mean() e std()
    grouped = df_filtered.groupby('Name')[elements].agg(['mean', 'std']).reset_index()
    
    # Appiattiamo il MultiIndex delle colonne (es: ('C', 'mean') -> 'C_mean')
    grouped.columns = ['Name'] + [f"{el}_{stat}" for el in elements for stat in ['mean', 'std']]
    
    # Riempi NaN nella Dev Standard con 0 (es. quando c'è solo 1 replica)
    for el in elements:
        grouped[f"{el}_std"] = grouped[f"{el}_std"].fillna(0)
        # Riempi anche i mean nan (se colonna era tutta vuota)
        grouped[f"{el}_mean"] = grouped[f"{el}_mean"].fillna(0)

    # --- Calcolo O2 ---
    o2_means = []
    o2_stds = []
    
    for _, row in grouped.iterrows():
        name = row['Name']
        sum_chns = row['C_mean'] + row['H_mean'] + row['N_mean'] + row['S_mean']
        
        # Calcolo SD per somma (propagazione errori semplificata se indipendenti)
        # SD_tot = sqrt(SD_C^2 + SD_H^2 + SD_N^2 + SD_S^2)
        var_sum = (row['C_std']**2 + row['H_std']**2 + row['N_std']**2 + row['S_std']**2)
        sd_o2 = np.sqrt(var_sum)
        
        if ignore_am:
            o2_val = 100 - sum_chns
        else:
            # Assumiamo 0 se il campo è rimasto vuoto/non trovato nel dict
            umidita = am_dict.get(name, {}).get('Umidità', 0.0) or 0.0
            ceneri = am_dict.get(name, {}).get('Ceneri', 0.0) or 0.0
            o2_val = 100 - sum_chns - umidita - ceneri
            
        # Non permettere O2 negativo (possibile se dati sballati)
        o2_means.append(max(0, o2_val))
        o2_stds.append(sd_o2)
        
    grouped['O2_mean'] = o2_means
    grouped['O2_std'] = o2_stds
    
    # --- Creazione Foglio 2 (Solo Medie) ---
    cols_means = ['Name', 'N_mean', 'C_mean', 'H_mean', 'S_mean', 'O2_mean']
    means_only_df = grouped[cols_means].copy()
    means_only_df.columns = ['Name', 'N (%)', 'C (%)', 'H (%)', 'S (%)', 'O2 (%)']
    
    if not ignore_am:
        # Aggiungiamo umidità e ceneri alla fine
        means_only_df['Moisture (%)'] = [am_dict.get(n, {}).get('Umidità', 0.0) or 0.0 for n in grouped['Name']]
        means_only_df['Ash (%)'] = [am_dict.get(n, {}).get('Ceneri', 0.0) or 0.0 for n in grouped['Name']]

    # --- Creazione Foglio 3 (Pretty / Formattato) ---
    pretty_df = pd.DataFrame()
    pretty_df['Name'] = grouped['Name']
    
    for el in ['N', 'C', 'H', 'S', 'O2']:
        pretty_df[f"{el} (%)"] = grouped.apply(
            lambda x: f"{x[el+'_mean']:.2f} ± {x[el+'_std']:.2f}", axis=1
        )
        
    if not ignore_am:
        # Aggiungiamo umidità e ceneri alla fine (senza SD in quanto input utente singolo)
        pretty_df['Moisture (%)'] = [f"{(am_dict.get(n, {}).get('Umidità', 0.0) or 0.0):.2f}" for n in grouped['Name']]
        pretty_df['Ash (%)'] = [f"{(am_dict.get(n, {}).get('Ceneri', 0.0) or 0.0):.2f}" for n in grouped['Name']]

    return grouped, pretty_df, means_only_df
