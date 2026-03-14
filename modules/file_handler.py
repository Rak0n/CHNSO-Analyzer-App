import pandas as pd
import streamlit as st
import io

@st.cache_data(show_spinner=False)
def load_excel_files(uploaded_files):
    all_data = []
    
    for file in uploaded_files:
        try:
            # 1. Legge TUTTO il foglio come matrice pura (header=None)
            df_raw = pd.read_excel(file, sheet_name="Element % Results", header=None)
            
            header_idx = None
            
            # 2. Scansiona ogni riga finché non trova quella che contiene 'Name' o 'Sample Name'
            for i, row in df_raw.iterrows():
                row_strs = [str(x).strip().lower() for x in row.values]
                if 'name' in row_strs or 'sample name' in row_strs:
                    header_idx = i
                    break
            
            if header_idx is None:
                st.error(f"Errore: Non sono riuscito a trovare la parola 'Name' nel file {file.name}.")
                continue
                
            # 3. Mappatura precisa delle colonne (Reverse Engineering del tuo file)
            # Il tuo file ha una prima colonna vuota che Pandas legge come 'nan'
            raw_columns = df_raw.iloc[header_idx].values
            clean_columns = []
            
            for idx, col_name in enumerate(raw_columns):
                col_str = str(col_name).strip()
                
                # Se è la colonna del nome, la standardizziamo
                if col_str.lower() in ['name', 'sample name']:
                    clean_columns.append('Name')
                # Se la colonna è vuota (come la colonna 0 del tuo file) diamo un nome fittizio
                elif col_str.lower() == 'nan' or col_str == '':
                    clean_columns.append(f"Vuota_{idx}")
                else:
                    clean_columns.append(col_str)
            
            # 4. Creiamo il dataframe usando i dati da header_idx in poi
            df = df_raw.iloc[header_idx + 1:].copy()
            df.columns = clean_columns
            
            # 5. Pulizia dei valori: Trasformiamo i '-' del tuo strumento in valori numerici nulli (NaN)
            cols_to_clean = ['N', 'C', 'H', 'S']
            for col in cols_to_clean:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                    
            # 6. Pulizia di righe vuote strumentali (ESCLUSIVA PER QUESTO FILE)
            if 'Name' in df.columns:
                df = df.dropna(subset=['Name'])
                df = df[df['Name'].astype(str).str.lower() != 'nan']
                all_data.append(df)
            else:
                st.error(f"Errore: Impossibile definire la colonna 'Name' nel file {file.name}")
            
        except Exception as e:
            st.error(f"Errore imprevisto nella lettura del file {file.name}: {e}")
            
    # --- Unione finale dei file validi ---
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
        
        # Foglio 1: Raw Data
        cols_raw = ['Type', 'Name', 'Weight', 'N', 'C', 'H', 'S']
        available_cols = [c for c in cols_raw if c in df_raw.columns]
        
        df_raw[available_cols].to_excel(writer, sheet_name='1 - Raw Data', index=False)
        
        # Foglio 2: Solo Medie
        df_means.to_excel(writer, sheet_name='2 - Means Only', index=False)
        
        # Foglio 3: Formattato (Media ± SD)
        df_pretty.to_excel(writer, sheet_name='3 - Summary Formatted', index=False)
        
        # Estetica
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
