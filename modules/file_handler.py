import pandas as pd
import streamlit as st
import io

@st.cache_data(show_spinner=False)
def load_excel_files(uploaded_files):
    """
    Legge i file caricati, trova la riga di intestazione e unisce i dati in un unico DataFrame.
    """
    all_data = []
    
    for file in uploaded_files:
        # Leggiamo un blocco per trovare dove inizia l'header vero
        try:
            df_temp = pd.read_excel(file, sheet_name="Element % Results", nrows=30, header=None)
            
            header_idx = 0
            # Cerca la riga che contiene sia 'Name' che 'C'
            for i, row in df_temp.iterrows():
                row_str = [str(x).strip() for x in row.values]
                if 'Name' in row_str and 'C' in row_str:
                    header_idx = i
                    break
            
            # Ora carichiamo i dati veri saltando le righe inutili
            df = pd.read_excel(file, sheet_name="Element % Results", skiprows=header_idx)
            
            # Pulizia di base: Convertiamo i '-' in NaN e poi in float per le colonne di interesse
            cols_to_clean = ['N', 'C', 'H', 'S']
            for col in cols_to_clean:
                if col in df.columns:
                    # Coerce trasforma eventuali stringhe (es: '-') in NaN
                    df[col] = pd.to_numeric(df[col], errors='coerce') 
            
            all_data.append(df)
            
        except Exception as e:
            st.error(f"Errore nella lettura del file {file.name}: {e}")
            
    if all_data:
        combined_df = pd.concat(all_data, ignore_index=True)
        # Rimuovi righe senza nome o che sono righe vuote
        combined_df = combined_df.dropna(subset=['Name'])
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
        cols_raw = ['Type', 'Name', 'Weight'] + [c for c in ['N', 'C', 'H', 'S'] if c in df_raw.columns]
        # Teniamo solo le colonne che effettivamente esistono
        cols_raw = [c for c in cols_raw if c in df_raw.columns]
        df_raw[cols_raw].to_excel(writer, sheet_name='1 - Raw Data', index=False)
        
        # Foglio 2: Solo Medie
        df_means.to_excel(writer, sheet_name='2 - Means Only', index=False)
        
        # Foglio 3: Formattato (Media ± SD)
        df_pretty.to_excel(writer, sheet_name='3 - Summary Formatted', index=False)
        
        # --- Formattazione estetica (Opzionale ma fa la differenza) ---
        workbook = writer.book
        
        # Formato per intestazioni
        header_format = workbook.add_format({
            'bold': True, 'text_wrap': True, 'valign': 'top', 
            'fg_color': '#D7E4BC', 'border': 1
        })
        
        # Applica formati per ogni worksheet
        for sheet_name in writer.sheets:
            worksheet = writer.sheets[sheet_name]
            # Imposta larghezza colonna Name
            worksheet.set_column('A:A', 30)
            worksheet.set_column('B:Z', 15)
            
            # Recupera il dataframe corrispondente per colorare l'header
            if sheet_name == '1 - Raw Data':
                df_ref = df_raw[cols_raw]
            elif sheet_name == '2 - Means Only':
                df_ref = df_means
            else:
                df_ref = df_pretty
                
            for col_num, value in enumerate(df_ref.columns.values):
                worksheet.write(0, col_num, value, header_format)

    output.seek(0)
    return output
