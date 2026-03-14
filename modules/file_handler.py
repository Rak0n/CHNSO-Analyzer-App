import pandas as pd
import streamlit as st
import io

@st.cache_data(show_spinner=False)
def load_excel_files(uploaded_files):
    """
    Legge i file caricati, trova la riga di intestazione in modo robusto 
    e unisce i dati in un unico DataFrame pulito.
    """
    all_data = []
    
    for file in uploaded_files:
        try:
            # Leggiamo un blocco di 30 righe per trovare dove inizia l'header vero
            df_temp = pd.read_excel(file, sheet_name="Element % Results", nrows=30, header=None)
            
            header_idx = 0
            # Cerca la riga che contiene 'name' (case insensitive e senza spazi)
            for i, row in df_temp.iterrows():
                row_str = [str(x).strip().lower() for x in row.values]
                if 'name' in row_str:
                    header_idx = i
                    break
            
            # Ora carichiamo i dati veri saltando le righe inutili
            df = pd.read_excel(file, sheet_name="Element % Results", skiprows=header_idx)
            
            # --- FIX CRUCIALE ---
            # Gli strumenti spesso inseriscono spazi invisibili nei nomi delle colonne (es: "Name "). 
            # Li rimuoviamo tutti forzatamente.
            df.columns = [str(col).strip() for col in df.columns]
            
            # Pulizia di base: Convertiamo i '-' in NaN e poi in float per le colonne elementari
            cols_to_clean = ['N', 'C', 'H', 'S']
            for col in cols_to_clean:
                if col in df.columns:
                    # pd.to_numeric converte automaticamente le stringhe non valide (es '-') in NaN
                    df[col] = pd.to_numeric(df[col], errors='coerce') 
            
            all_data.append(df)
            
        except Exception as e:
            st.error(f"Errore nella lettura del file {file.name}: {e}")
            
    if all_data:
        combined_df = pd.concat(all_data, ignore_index=True)
        
        # Controllo di sicurezza finale prima del dropna
        if 'Name' in combined_df.columns:
            # Rimuovi righe senza nome o che sono righe vuote strumentali
            combined_df = combined_df.dropna(subset=['Name'])
        else:
            st.error("Errore critico: Impossibile identificare la colonna 'Name'. Formato Excel non riconosciuto.")
            
        return combined_df
    else:
        return pd.DataFrame()

def create_excel_download(df_raw, df_means, df_pretty, ignore_am):
    """
    Crea un file Excel in memoria con 3 fogli.
    Restituisce un buffer BytesIO pronto per il download tramite Streamlit.
    """
    output = io.BytesIO()
    
    # Usiamo xlsxwriter come motore
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        
        # Foglio 1: Raw Data (solo le colonne utili)
        cols_raw = ['Type', 'Name', 'Weight', 'N', 'C', 'H', 'S']
        # Teniamo solo le colonne che effettivamente esistono nel df_raw (evita KeyError)
        available_cols = [c for c in cols_raw if c in df_raw.columns]
        
        df_raw[available_cols].to_excel(writer, sheet_name='1 - Raw Data', index=False)
        
        # Foglio 2: Solo Medie
        df_means.to_excel(writer, sheet_name='2 - Means Only', index=False)
        
        # Foglio 3: Formattato (Media ± SD)
        df_pretty.to_excel(writer, sheet_name='3 - Summary Formatted', index=False)
        
        # --- Formattazione estetica ---
        workbook = writer.book
        
        # Formato per intestazioni
        header_format = workbook.add_format({
            'bold': True, 'text_wrap': True, 'valign': 'top', 
            'fg_color': '#D7E4BC', 'border': 1
        })
        
        # Applica formati per ogni worksheet
        for sheet_name in writer.sheets:
            worksheet = writer.sheets[sheet_name]
            # Imposta larghezza colonne
            worksheet.set_column('A:A', 30)
            worksheet.set_column('B:Z', 15)
            
            # Recupera il dataframe corrispondente per colorare l'header
            if sheet_name == '1 - Raw Data':
                df_ref = df_raw[available_cols]
            elif sheet_name == '2 - Means Only':
                df_ref = df_means
            else:
                df_ref = df_pretty
                
            for col_num, value in enumerate(df_ref.columns.values):
                worksheet.write(0, col_num, value, header_format)

    output.seek(0)
    return output
