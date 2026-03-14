import pandas as pd
import streamlit as st
import io

@st.cache_data(show_spinner=False)
def load_excel_files(uploaded_files):
    all_data = []
    
    for file in uploaded_files:
        try:
            # 1. Legge TUTTO il foglio ignorando le intestazioni per avere una matrice pura
            df_raw = pd.read_excel(file, sheet_name="Element % Results", header=None)
            
            header_idx = None
            
            # 2. Scansiona ogni singola riga per trovare l'intestazione corretta
            for i, row in df_raw.iterrows():
                # Converte la riga in stringhe minuscole, rimuovendo spazi
                row_strs = [str(x).strip().lower() for x in row.values]
                
                # Se la riga contiene 'name', abbiamo trovato la riga dei titoli
                if 'name' in row_strs or 'sample name' in row_strs:
                    header_idx = i
                    break
            
            if header_idx is None:
                st.error(f"Errore: Non sono riuscito a trovare la parola 'Name' nel file {file.name}.")
                continue
                
            # 3. Estrae i veri nomi delle colonne dalla riga trovata
            columns = [str(x).strip() for x in df_raw.iloc[header_idx].values]
            
            # 4. Isola solo i dati veri (le righe successive all'intestazione)
            df = df_raw.iloc[header_idx + 1:].copy()
            df.columns = columns
            
            # 5. Rinomina esplicitamente la colonna in 'Name' (nel caso in cui fosse 'Sample Name')
            for col in df.columns:
                if str(col).lower() == 'name' or str(col).lower() == 'sample name':
                    df.rename(columns={col: 'Name'}, inplace=True)
                    break
            
            # 6. Pulisce i dati elementari (trasforma i '-' in celle vuote matematiche)
            cols_to_clean = ['N', 'C', 'H', 'S']
            for col in cols_to_clean:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                    
            all_data.append(df)
            
        except Exception as e:
            st.error(f"Errore imprevisto nella lettura del file {file.name}: {e}")
            
    # --- Unione finale dei file ---
    if all_data:
        combined_df = pd.concat(all_data, ignore_index=True)
        
        # Sicurezza assoluta: verifica che 'Name' esista prima di operare
        if 'Name' in combined_df.columns:
            # Elimina le righe vuote strumentali
            combined_df = combined_df.dropna(subset=['Name'])
            # Elimina eventuali righe in cui Name è letto come stringa 'nan'
            combined_df = combined_df[combined_df['Name'].astype(str).str.lower() != 'nan']
        else:
            st.error("Errore critico post-unione: La colonna 'Name' è andata persa.")
            
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
