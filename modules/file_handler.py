import pandas as pd
import streamlit as st
import io

@st.cache_data(show_spinner=False)
def load_excel_files(uploaded_files):
    all_data = []
    
    for file in uploaded_files:
        try:
            # Forza la lettura SOLO del PRIMO foglio come matrice grezza
            df_raw = pd.read_excel(file, sheet_name=0, header=None)
            
            header_idx = None
            for i, row in df_raw.iterrows():
                row_strs = [str(x).strip().lower() for x in row.values]
                if 'name' in row_strs:
                    header_idx = i
                    break
            
            if header_idx is None:
                st.error(f"Errore: Non sono riuscito a trovare la colonna 'Name' nel file {file.name}.")
                continue
                
            raw_columns = df_raw.iloc[header_idx].values
            clean_columns = []
            
            for idx, col_name in enumerate(raw_columns):
                col_str = str(col_name).strip()
                col_lower = col_str.lower()
                
                if col_lower == 'name': clean_columns.append('Name')
                elif col_lower == 'weight (mg)': clean_columns.append('Weight')
                elif col_lower == 'n %': clean_columns.append('N')
                elif col_lower == 'c %': clean_columns.append('C')
                elif col_lower == 'h %': clean_columns.append('H')
                elif col_lower == 's %': clean_columns.append('S')
                elif col_lower == 'type': clean_columns.append('Type')
                else: clean_columns.append(f"Ignora_{idx}")
            
            df = df_raw.iloc[header_idx + 1:].copy()
            df.columns = clean_columns
            
            for required_col in ['N', 'C', 'H', 'S']:
                if required_col not in df.columns:
                    df[required_col] = 0.0
            
            cols_to_clean = ['N', 'C', 'H', 'S']
            for col in cols_to_clean:
                df[col] = df[col].astype(str).str.strip().replace('-', '0')
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
                    
            if 'Name' in df.columns:
                df = df.dropna(subset=['Name'])
                df = df[df['Name'].astype(str).str.lower() != 'nan']
                all_data.append(df)
            
        except Exception as e:
            st.error(f"Errore nella lettura del file {file.name}: {e}")
            
    if all_data:
        combined_df = pd.concat(all_data, ignore_index=True)
        return combined_df
    else:
        return pd.DataFrame()

def create_excel_download(df_raw, selected_samples, am_dict, ignore_am):
    """
    Crea un Excel Interattivo! Scrive le formule native di Excel invece di valori statici,
    permettendo all'utente di modificare Umidità/Ceneri e vedere il ricalcolo istantaneo di O,
    Medie e Deviazioni Standard.
    """
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        workbook = writer.book
        
        # --- Foglio 1: Raw Data ---
        cols_raw = ['Type', 'Name', 'Weight', 'N', 'C', 'H', 'S']
        available_cols = [c for c in cols_raw if c in df_raw.columns]
        df_raw[available_cols].to_excel(writer, sheet_name='1 - Raw Data', index=False)
        ws_raw = writer.sheets['1 - Raw Data']
        
        # Mappatura lettere colonne Excel (es. N è la colonna D)
        col_letters = {col: chr(65 + idx) for idx, col in enumerate(available_cols)}
        
        # Analizziamo quali righe occupa ogni Sample nel Foglio 1 per costruire le formule AVERAGE/STDEV
        sample_ranges = {}
        current_row = 2 # Inizia da riga 2 (dopo l'header)
        for sample in selected_samples:
            count = len(df_raw[df_raw['Name'] == sample])
            if count > 0:
                sample_ranges[sample] = (current_row, current_row + count - 1)
                current_row += count

        # Stili Excel
        header_format = workbook.add_format({
            'bold': True, 'text_wrap': True, 'valign': 'top', 
            'fg_color': '#D7E4BC', 'border': 1
        })
        num_format = workbook.add_format({'num_format': '0.00'}) # Formato numerico a 2 decimali
        
        # --- Foglio 2: Means Only (Formule Vive) ---
        ws_means = workbook.add_worksheet('2 - Means Only')
        if ignore_am:
            headers_means = ['Name', 'N (%)', 'C (%)', 'H (%)', 'S (%)', 'O (%)']
        else:
            headers_means = ['Name', 'N (%)', 'C (%)', 'H (%)', 'S (%)', 'Moisture (%)', 'Ash (%)', 'O (%)']
            
        for c_idx, header in enumerate(headers_means):
            ws_means.write(0, c_idx, header, header_format)
            
        for r_idx, sample in enumerate(selected_samples):
            row = r_idx + 1         # Indice python (0-based) per scrivere
            row_exc = row + 1       # Numero riga Excel (1-based) per la formula
            ws_means.write_string(row, 0, sample)
            
            if sample in sample_ranges:
                start, end = sample_ranges[sample]
                
                # Formule per CHNS: =AVERAGE('1 - Raw Data'!D2:D4)
                for c_offset, el in enumerate(['N', 'C', 'H', 'S']):
                    if el in col_letters:
                        letter = col_letters[el]
                        formula = f"=AVERAGE('1 - Raw Data'!{letter}{start}:{letter}{end})"
                        ws_means.write_formula(row, c_offset + 1, formula, num_format)
                    else:
                        ws_means.write_number(row, c_offset + 1, 0.0, num_format)
                
                # Variabili inserite a mano e Calcolo O Interattivo: =100-B2-C2-D2-E2-F2-G2
                if not ignore_am:
                    moisture = am_dict.get(sample, {}).get('Umidità', 0.0) or 0.0
                    ash = am_dict.get(sample, {}).get('Ceneri', 0.0) or 0.0
                    ws_means.write_number(row, 5, moisture, num_format)
                    ws_means.write_number(row, 6, ash, num_format)
                    # Formula MAX per impedire Ossigeno negativo
                    formula_o = f"=MAX(0, 100-B{row_exc}-C{row_exc}-D{row_exc}-E{row_exc}-F{row_exc}-G{row_exc})"
                    ws_means.write_formula(row, 7, formula_o, num_format)
                else:
                    formula_o = f"=MAX(0, 100-B{row_exc}-C{row_exc}-D{row_exc}-E{row_exc})"
                    ws_means.write_formula(row, 5, formula_o, num_format)

        # --- Foglio 3: Summary Formatted (Formule Vive per Media ± SD) ---
        ws_pretty = workbook.add_worksheet('3 - Summary Formatted')
        if ignore_am:
            headers_pretty = ['Name', 'N (%)', 'C (%)', 'H (%)', 'S (%)', 'O (%)']
        else:
            headers_pretty = ['Name', 'N (%)', 'C (%)', 'H (%)', 'S (%)', 'O (%)', 'Moisture (%)', 'Ash (%)']
            
        for c_idx, header in enumerate(headers_pretty):
            ws_pretty.write(0, c_idx, header, header_format)
            
        for r_idx, sample in enumerate(selected_samples):
            row = r_idx + 1
            row_exc = row + 1
            ws_pretty.write_string(row, 0, sample)
            
            if sample in sample_ranges:
                start, end = sample_ranges[sample]
                
                # Formula concatenata: =TEXT(Media, "0.00") & " ± " & TEXT(STDEV, "0.00")
                # IFERROR serve nel caso ci sia 1 sola replica (che manderebbe in crash la dev standard)
                elements = ['N', 'C', 'H', 'S']
                for c_offset, el in enumerate(elements):
                    letter_means = chr(66 + c_offset) # Le medie nel foglio 2 sono in B, C, D, E
                    if el in col_letters:
                        letter_raw = col_letters[el]
                        formula = f'=TEXT(\'2 - Means Only\'!{letter_means}{row_exc}, "0.00") & " ± " & TEXT(IFERROR(STDEV.S(\'1 - Raw Data\'!{letter_raw}{start}:{letter_raw}{end}), 0), "0.00")'
                    else:
                        formula = f'=TEXT(\'2 - Means Only\'!{letter_means}{row_exc}, "0.00") & " ± 0.00"'
                    ws_pretty.write_formula(row, c_offset + 1, formula)
                
                # Propagazione errore Ossigeno nel Foglio 3 (Radice della somma delle Varianze)
                letter_o_means = 'H' if not ignore_am else 'F'
                var_parts = []
                for el in elements:
                    if el in col_letters:
                        letter_raw = col_letters[el]
                        var_parts.append(f"VAR.S('1 - Raw Data'!{letter_raw}{start}:{letter_raw}{end})")
                
                if var_parts:
                    var_sum = "+".join(var_parts)
                    formula_o = f'=TEXT(\'2 - Means Only\'!{letter_o_means}{row_exc}, "0.00") & " ± " & TEXT(IFERROR(SQRT({var_sum}), 0), "0.00")'
                else:
                    formula_o = f'=TEXT(\'2 - Means Only\'!{letter_o_means}{row_exc}, "0.00") & " ± 0.00"'
                
                ws_pretty.write_formula(row, 5, formula_o)
                
                # Link diretti a Umidità e Ceneri
                if not ignore_am:
                    formula_m = f'=TEXT(\'2 - Means Only\'!F{row_exc}, "0.00")'
                    formula_a = f'=TEXT(\'2 - Means Only\'!G{row_exc}, "0.00")'
                    ws_pretty.write_formula(row, 6, formula_m)
                    ws_pretty.write_formula(row, 7, formula_a)

        # Aggiustamenti estetiche larghezze per tutti i fogli
        for ws in [ws_raw, ws_means, ws_pretty]:
            ws.set_column('A:A', 30)
            ws.set_column('B:Z', 15)
            
        for col_num, value in enumerate(available_cols):
            ws_raw.write(0, col_num, value, header_format)

    output.seek(0)
    return output
