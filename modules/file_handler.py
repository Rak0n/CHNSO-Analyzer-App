import pandas as pd
import streamlit as st
import io

@st.cache_data(show_spinner=False)
def load_excel_files(uploaded_files):
    all_data = []
    for file in uploaded_files:
        try:
            df_raw = pd.read_excel(file, sheet_name=0, header=None)
            header_idx = None
            for i, row in df_raw.iterrows():
                row_strs = [str(x).strip().lower() for x in row.values]
                if 'name' in row_strs:
                    header_idx = i
                    break
            
            if header_idx is None: continue
                
            raw_columns = df_raw.iloc[header_idx].values
            clean_columns = []
            for idx, col_name in enumerate(raw_columns):
                col_lower = str(col_name).strip().lower()
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
                if required_col not in df.columns: df[required_col] = 0.0
            
            for col in ['N', 'C', 'H', 'S']:
                df[col] = df[col].astype(str).str.strip().replace('-', '0')
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
                    
            if 'Name' in df.columns:
                df = df.dropna(subset=['Name'])
                df = df[df['Name'].astype(str).str.lower() != 'nan']
                all_data.append(df)
        except:
            continue
            
    if all_data: return pd.concat(all_data, ignore_index=True)
    return pd.DataFrame()

def load_existing_report(uploaded_file):
    """
    Legge un report generato dall'app in precedenza ed estrae i dati facendo reverse-engineering.
    Separa le stringhe 'Media ± SD' dal foglio 3 e prende i parametri avanzati dal foglio 2.
    """
    try:
        df_means = pd.read_excel(uploaded_file, sheet_name='2 - Means Only')
        df_pretty = pd.read_excel(uploaded_file, sheet_name='3 - Summary Formatted')
        
        stats_data = {'Name': df_means['Name'].tolist()}
        
        # 1. Estrazione Medie e SD (spacchettando "Media ± SD") dal Foglio 3
        for el in ['C', 'H', 'N', 'S', 'O']:
            col_name = f"{el} (%)"
            means, stds = [], []
            if col_name in df_pretty.columns:
                for val in df_pretty[col_name]:
                    try:
                        if isinstance(val, str) and '±' in val:
                            parts = val.split('±')
                            means.append(float(parts[0].strip().replace(',', '.')))
                            stds.append(float(parts[1].strip().replace(',', '.')))
                        else:
                            means.append(float(val) if pd.notnull(val) else 0.0)
                            stds.append(0.0)
                    except:
                        means.append(0.0)
                        stds.append(0.0)
            else:
                means = [0.0] * len(df_means)
                stds = [0.0] * len(df_means)
            
            stats_data[f"{el}_mean"] = means
            stats_data[f"{el}_std"] = stds
            
        # 2. Estrazione parametri singoli (Umidità, HHV, Rapporti) dal Foglio 2
        mappings = [
            ('Moisture (%)', 'Moisture_mean'), ('Ash (%)', 'Ash_mean'),
            ('HHV (MJ/Kg)', 'HHV_mean'), ('N/C', 'NC_mean'),
            ('H/C', 'HC_mean'), ('O/C', 'OC_mean')
        ]
        
        for col_excel, col_target in mappings:
            if col_excel in df_means.columns:
                stats_data[col_target] = pd.to_numeric(df_means[col_excel], errors='coerce').fillna(0.0).tolist()
            else:
                stats_data[col_target] = [0.0] * len(df_means)
                
        return pd.DataFrame(stats_data)
        
    except Exception as e:
        st.error(f"Errore nella lettura del report. Assicurati di aver caricato un report completo a 3 fogli. Dettagli tecnici: {e}")
        return None

def create_excel_download(df_raw, selected_samples, am_dict, ignore_am):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        workbook = writer.book
        
        # Foglio 1
        cols_raw = ['Type', 'Name', 'Weight', 'N', 'C', 'H', 'S']
        available_cols = [c for c in cols_raw if c in df_raw.columns]
        df_raw[available_cols].to_excel(writer, sheet_name='1 - Raw Data', index=False)
        ws_raw = writer.sheets['1 - Raw Data']
        col_letters = {col: chr(65 + idx) for idx, col in enumerate(available_cols)}
        
        sample_ranges = {}
        current_row = 2
        for sample in selected_samples:
            count = len(df_raw[df_raw['Name'] == sample])
            if count > 0:
                sample_ranges[sample] = (current_row, current_row + count - 1)
                current_row += count

        header_format = workbook.add_format({'bold': True, 'text_wrap': True, 'valign': 'top', 'fg_color': '#D7E4BC', 'border': 1})
        num_format = workbook.add_format({'num_format': '0.00'})
        ratio_format = workbook.add_format({'num_format': '0.000'})
        
        # --- Foglio 2 ---
        ws_means = workbook.add_worksheet('2 - Means Only')
        headers_means = ['Name', 'N (%)', 'C (%)', 'H (%)', 'S (%)']
        if not ignore_am: headers_means.extend(['Moisture (%)', 'Ash (%)'])
        headers_means.append('O (%)')
        headers_means.extend(['HHV (MJ/Kg)', 'N/C', 'H/C', 'O/C'])
            
        for c_idx, header in enumerate(headers_means):
            ws_means.write(0, c_idx, header, header_format)
            
        for r_idx, sample in enumerate(selected_samples):
            row, row_exc = r_idx + 1, r_idx + 2
            ws_means.write_string(row, 0, sample)
            
            if sample in sample_ranges:
                start, end = sample_ranges[sample]
                for c_offset, el in enumerate(['N', 'C', 'H', 'S']):
                    if el in col_letters:
                        ws_means.write_formula(row, c_offset + 1, f"=AVERAGE('1 - Raw Data'!{col_letters[el]}{start}:{col_letters[el]}{end})", num_format)
                    else:
                        ws_means.write_number(row, c_offset + 1, 0.0, num_format)
                
                if not ignore_am:
                    ws_means.write_number(row, 5, am_dict.get(sample, {}).get('Umidità', 0.0) or 0.0, num_format)
                    ws_means.write_number(row, 6, am_dict.get(sample, {}).get('Ceneri', 0.0) or 0.0, num_format)
                    ws_means.write_formula(row, 7, f"=MAX(0, 100-B{row_exc}-C{row_exc}-D{row_exc}-E{row_exc}-F{row_exc}-G{row_exc})", num_format)
                    adv_start_col = 8
                    letter_o = 'H'
                else:
                    ws_means.write_formula(row, 5, f"=MAX(0, 100-B{row_exc}-C{row_exc}-D{row_exc}-E{row_exc})", num_format)
                    adv_start_col = 6
                    letter_o = 'F'

                ws_means.write_formula(row, adv_start_col, f"=MAX(0, 0.3491*C{row_exc}+1.1783*D{row_exc}+0.1005*E{row_exc}-0.1034*{letter_o}{row_exc}-0.0151*B{row_exc})", num_format)
                ws_means.write_formula(row, adv_start_col+1, f"=IFERROR((B{row_exc}/14.007)/(C{row_exc}/12.011), 0)", ratio_format)
                ws_means.write_formula(row, adv_start_col+2, f"=IFERROR((D{row_exc}/1.008)/(C{row_exc}/12.011), 0)", ratio_format)
                ws_means.write_formula(row, adv_start_col+3, f"=IFERROR(({letter_o}{row_exc}/16)/(C{row_exc}/12.011), 0)", ratio_format)

        # --- Foglio 3 ---
        ws_pretty = workbook.add_worksheet('3 - Summary Formatted')
        headers_pretty = ['Name', 'N (%)', 'C (%)', 'H (%)', 'S (%)', 'O (%)']
        if not ignore_am: headers_pretty.extend(['Moisture (%)', 'Ash (%)'])
        for c_idx, header in enumerate(headers_pretty): ws_pretty.write(0, c_idx, header, header_format)
            
        for r_idx, sample in enumerate(selected_samples):
            row, row_exc = r_idx + 1, r_idx + 2
            ws_pretty.write_string(row, 0, sample)
            if sample in sample_ranges:
                start, end = sample_ranges[sample]
                for c_offset, el in enumerate(['N', 'C', 'H', 'S']):
                    letter_means = chr(66 + c_offset)
                    if el in col_letters:
                        ws_pretty.write_formula(row, c_offset + 1, f'=TEXT(\'2 - Means Only\'!{letter_means}{row_exc}, "0.00") & " ± " & TEXT(IFERROR(STDEV.S(\'1 - Raw Data\'!{col_letters[el]}{start}:{col_letters[el]}{end}), 0), "0.00")')
                    else:
                        ws_pretty.write_formula(row, c_offset + 1, f'=TEXT(\'2 - Means Only\'!{letter_means}{row_exc}, "0.00") & " ± 0.00"')
                
                letter_o_means = 'H' if not ignore_am else 'F'
                var_parts = [f"VAR.S('1 - Raw Data'!{col_letters[el]}{start}:{col_letters[el]}{end})" for el in ['N', 'C', 'H', 'S'] if el in col_letters]
                
                if var_parts:
                    ws_pretty.write_formula(row, 5, f'=TEXT(\'2 - Means Only\'!{letter_o_means}{row_exc}, "0.00") & " ± " & TEXT(IFERROR(SQRT({"+".join(var_parts)}), 0), "0.00")')
                else:
                    ws_pretty.write_formula(row, 5, f'=TEXT(\'2 - Means Only\'!{letter_o_means}{row_exc}, "0.00") & " ± 0.00"')
                
                if not ignore_am:
                    ws_pretty.write_formula(row, 6, f'=TEXT(\'2 - Means Only\'!F{row_exc}, "0.00")')
                    ws_pretty.write_formula(row, 7, f'=TEXT(\'2 - Means Only\'!G{row_exc}, "0.00")')

        for ws in [ws_raw, ws_means, ws_pretty]:
            ws.set_column('A:A', 30)
            ws.set_column('B:Z', 15)
        for col_num, value in enumerate(available_cols): ws_raw.write(0, col_num, value, header_format)

    output.seek(0)
    return output
