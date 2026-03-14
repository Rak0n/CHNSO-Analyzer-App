import pandas as pd
import streamlit as st
import io

@st.cache_data(show_spinner=False)
def load_excel_files(uploaded_files):
    all_data = []
    
    for file in uploaded_files:
        try:
            # 1. Forza la lettura SOLO del PRIMO foglio (sheet_name=0)
            # Legge come matrice grezza per non farsi ingannare dai metadati
            df_raw = pd.read_excel(file, sheet_name=0, header=None)
            
            header_idx = None
            
            # 2. Scansiona ogni riga finché non trova la riga delle intestazioni ("Name")
            for i, row in df_raw.iterrows():
                row_strs = [str(x).strip().lower() for x in row.values]
                if 'name' in row_strs:
                    header_idx = i
                    break
            
            if header_idx is None:
                st.error(f"Errore: Non sono riuscito a trovare la colonna 'Name' nel file {file.name}.")
                continue
                
            # 3. Mappatura SU MISURA basata sull'esatto layout che mi hai fornito
            # Layout: Pos.# | Type | Name | Weight (mg) | N % | C % | H % | S % | O %
            raw_columns = df_raw.iloc[header_idx].values
            clean_columns = []
            
            for idx, col_name in enumerate(raw_columns):
                col_str = str(col_name).strip()
                col_lower = col_str.lower()
                
                # Associazione chirurgica
                if col_lower == 'name':
                    clean_columns.append('Name')
                elif col_lower == 'weight (mg)':
                    clean_columns.append('Weight')
                elif col_lower == 'n %':
                    clean_columns.append('N')
                elif col_lower == 'c %':
                    clean_columns.append('C')
                elif col_lower == 'h %':
                    clean_columns.append('H')
                elif col_lower == 's %':
                    clean_columns.append('S')
                elif col_lower == 'type':
                    clean_columns.append('Type')
                else:
                    # Colonne vuote o la colonna O % vengono messe in un cestino virtuale
                    clean_columns.append(f"Ignora_{idx}")
            
            # 4. Applica i nomi puliti e taglia i metadati in alto (Autorun, Date, ecc.)
            df = df_raw.iloc[header_idx + 1:].copy()
            df.columns = clean_columns
            
            # 5. GARANZIA COLONNE
            # Assicuriamoci che N, C, H, S esistano sempre, anche se vuoti
            for required_col in ['N', 'C', 'H', 'S']:
                if required_col not in df.columns:
                    df[required_col] = 0.0
            
            # 6. Conversione del "-" in "0" come richiesto
            cols_to_clean = ['N', 'C', 'H', 'S']
            for col in cols_to_clean:
                # Se c'è un trattino, diventa 0. Qualsiasi altra stringa strana diventa NaN e poi 0
                df[col] = df[col].astype(str).str.strip().replace('-', '0')
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
                    
            # 7. Filtraggio finale (teniamo solo le righe con un Sample Name valido)
            if 'Name' in df.columns:
                df = df.dropna(subset=['Name'])
                df = df[df['Name'].astype(str).str.lower() != 'nan']
                all_data.append(df)
            
        except Exception as e:
            st.error(f"Errore nella lettura del file {file.name}: {e}")
            
    # --- Unione finale dei file ---
    if all_data:
        combined_df = pd.concat(all_data, ignore_index=True)
        return combined_df
    else:
        return pd.DataFrame()

def create_excel_download(df_raw, df_means, df_pretty, ignore_am):
    """
    Crea un file Excel in memoria con 3 fogli e restituisce il buffer per il download.
    """
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        
        # Foglio 1: Raw Data (esportiamo solo da Type a S, saltando le colonne ignorate)
        cols_raw = ['Type', 'Name', 'Weight', 'N', 'C', 'H', 'S']
        available_cols = [c for c in cols_raw if c in df_raw.columns]
        
        df_raw[available_cols].to_excel(writer, sheet_name='1 - Raw Data', index=False)
        
        # Foglio 2: Solo Medie
        df_means.to_excel(writer, sheet_name='2 - Means Only', index=False)
        
        # Foglio 3: Formattato (Media ± SD)
        df_pretty.to_excel(writer, sheet_name='3 - Summary Formatted', index=False)
        
        # Estetica del file scaricato
        workbook = writer.book
        header_format = workbook.add_format({
            'bold': True, 'text_wrap': True, 'valign': 'top', 
            'fg_color': '#D7E4BC', 'border': 1
        })
        
        for sheet_name in writer.sheets:
            worksheet = writer.sheets[sheet_name]
            worksheet.set_column('A:A', 30)
            worksheet.set_column('B:Z', 15)
            
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
