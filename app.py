import streamlit as st
import pandas as pd
from modules import file_handler, data_processing, ui_components, visualizations

# Configurazione della pagina
st.set_page_config(page_title="CHNSO Analyzer", page_icon="🧪", layout="wide")

# Inizializzazione dello stato di sessione
if 'raw_data' not in st.session_state:
    st.session_state.raw_data = None
if 'processed_data' not in st.session_state:
    st.session_state.processed_data = None
if 'selected_samples' not in st.session_state:
    st.session_state.selected_samples = []

# --- Layout Intestazione con Logo ---
col1, col2 = st.columns([1, 5])
with col1:
    try:
        st.image("assets/logo.svg")
    except:
        st.title("🧪")
        
with col2:
    st.title("CHNSO Analyzer")
    st.markdown("Analisi automatizzata dei dati elementari, calcolo dell'Ossigeno ed esportazione avanzata.")

st.divider()

# Creazione delle schede (Tabs)
tab1, tab2, tab3, tab4 = st.tabs([
    "📂 1. Caricamento Dati", 
    "⚙️ 2. Calcoli e Umidità/Ceneri", 
    "📊 3. Dashboard Singola", 
    "⚖️ 4. Dashboard Confronto"
])

# --- TAB 1: Caricamento Dati ---
with tab1:
    # Nuova opzione per scegliere la modalità operativa
    app_mode = st.radio(
        "Modalità Operativa:", 
        ["🔬 Nuova Analisi (da dati grezzi)", "📂 Visualizza Report Esistente"], 
        horizontal=True
    )
    st.markdown("<br>", unsafe_allow_html=True)
    
    if "Nuova" in app_mode:
        uploaded_files = st.file_uploader(
            "Trascina qui i tuoi file Excel (.xlsx) estratti dallo strumento", 
            type=['xlsx'], 
            accept_multiple_files=True
        )

        if uploaded_files:
            with st.spinner("Lettura dei file in corso..."):
                df_raw = file_handler.load_excel_files(uploaded_files)
                
                if not df_raw.empty:
                    st.session_state.raw_data = df_raw
                    st.success("File caricati e uniti con successo!")
                    
                    all_samples = df_raw['Name'].dropna().unique().tolist()
                    
                    st.subheader("✅ 1. Selezione Sample")
                    st.write("Spunta la casella 'Seleziona' per includere il sample nell'analisi. Le caselle sono inizialmente vuote.")
                    
                    if 'selection_state' not in st.session_state or st.session_state.get('last_file') != df_raw.shape[0]:
                        st.session_state.selection_state = pd.DataFrame({
                            "Seleziona": [False] * len(all_samples),
                            "Sample": all_samples
                        })
                        st.session_state.last_file = df_raw.shape[0]

                    edited_selection = st.data_editor(
                        st.session_state.selection_state,
                        column_config={
                            "Seleziona": st.column_config.CheckboxColumn("Seleziona", default=False),
                            "Sample": st.column_config.TextColumn("Nome Sample", disabled=True)
                        },
                        hide_index=True,
                        use_container_width=True,
                        key="editor_selezioni"
                    )
                    
                    selected_unsorted = edited_selection[edited_selection["Seleziona"]]["Sample"].tolist()
                    
                    if selected_unsorted:
                        st.subheader("🔢 2. Anteprima Dati e Ordinamento")
                        st.write("Modifica il numero nella colonna 'Ordine' e clicca sull'intestazione per riordinare l'export.")
                        
                        if 'order_state' not in st.session_state or set(st.session_state.get('last_selected', [])) != set(selected_unsorted):
                            df_unique = pd.DataFrame({"Name": selected_unsorted})
                            df_unique["Ordine"] = range(1, len(selected_unsorted) + 1)
                            
                            preview_cols = [c for c in ['Weight', 'N', 'C', 'H', 'S'] if c in df_raw.columns]
                            df_first_raw = df_raw.drop_duplicates(subset=['Name']).copy()
                            df_order_preview = pd.merge(df_unique, df_first_raw[['Name'] + preview_cols], on='Name', how='left')
                            
                            st.session_state.order_state = df_order_preview
                            st.session_state.last_selected = selected_unsorted
                            
                        col_configs = {
                            "Ordine": st.column_config.NumberColumn("Ordine", min_value=1, step=1),
                            "Name": st.column_config.TextColumn("Nome Sample", disabled=True)
                        }
                        for col in [c for c in ['Weight', 'N', 'C', 'H', 'S'] if c in df_raw.columns]:
                            col_configs[col] = st.column_config.Column(disabled=True)

                        edited_order = st.data_editor(
                            st.session_state.order_state,
                            column_config=col_configs,
                            hide_index=True,
                            use_container_width=True,
                            key="editor_ordine"
                        )
                        
                        edited_order["Ordine"] = pd.to_numeric(edited_order["Ordine"], errors='coerce').fillna(999)
                        st.session_state.selected_samples = edited_order.sort_values(by="Ordine")["Name"].tolist()
                    else:
                        st.info("👆 Seleziona almeno un sample nella tabella sopra per sbloccare l'anteprima e ordinarli.")
                        st.session_state.selected_samples = []
    
    else: # Modalità "Carica Report Esistente"
        st.subheader("Visualizzazione Report")
        st.write("Hai già un file Excel scaricato da questa app in passato? Trascinalo qui per rivederne i grafici immediatamente.")
        
        uploaded_report = st.file_uploader(
            "Trascina qui il Report (es. CHNSO_Report_Analisi.xlsx)", 
            type=['xlsx'], 
            accept_multiple_files=False
        )
        
        if uploaded_report:
            with st.spinner("Estrazione dei dati e ricostruzione grafici in corso..."):
                stats_df = file_handler.load_existing_report(uploaded_report)
                
                if stats_df is not None and not stats_df.empty:
                    # Impostiamo i dati ricostruiti e puliamo raw_data per segnalare il "Read-Only" mode
                    st.session_state.raw_data = None
                    st.session_state.processed_data = {'stats': stats_df}
                    st.session_state.selected_samples = stats_df['Name'].tolist()
                    
                    st.success("✅ Report caricato e processato con successo! Vai alla Tab 3 o 4 per esplorare i grafici.")

# --- TAB 2: Calcoli ---
with tab2:
    if st.session_state.raw_data is not None and st.session_state.selected_samples:
        st.header("Impostazioni Ceneri e Umidità")
        
        ignore_ash_moisture = st.checkbox(
            "🚫 Trascura Ceneri e Umidità per questa sessione (Calcola O solo come 100 - CHNS)", 
            value=False
        )
        
        ash_moisture_data = ui_components.ash_moisture_form(
            st.session_state.selected_samples, 
            ignore_ash_moisture
        )
        
        if st.button("🚀 Esegui Calcoli", type="primary"):
            with st.spinner("Calcolo Medie, Deviazioni Standard e O..."):
                df_stats, df_pretty, df_means_only = data_processing.process_data(
                    st.session_state.raw_data, st.session_state.selected_samples, ash_moisture_data, ignore_ash_moisture
                )
                
                df_raw_filtered = st.session_state.raw_data[st.session_state.raw_data['Name'].isin(st.session_state.selected_samples)].copy()
                df_raw_filtered['__sort_col'] = pd.Categorical(df_raw_filtered['Name'], categories=st.session_state.selected_samples, ordered=True)
                df_raw_filtered = df_raw_filtered.sort_values('__sort_col').drop(columns=['__sort_col'])
                
                st.session_state.processed_data = {
                    'stats': df_stats, 'pretty': df_pretty, 'means': df_means_only,
                    'raw_filtered': df_raw_filtered, 'ignore_am': ignore_ash_moisture
                }
                
                st.success("Calcoli completati!")
                st.dataframe(df_pretty, use_container_width=True)
                
                excel_buffer = file_handler.create_excel_download(
                    st.session_state.processed_data['raw_filtered'], st.session_state.selected_samples, ash_moisture_data, ignore_ash_moisture
                )
                
                st.download_button(
                    label="📥 Scarica Report Excel",
                    data=excel_buffer, file_name="CHNSO_Report_Analisi.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
    
    # Messaggio di avviso intelligente se siamo in modalità caricamento report
    elif st.session_state.processed_data is not None and st.session_state.raw_data is None:
        st.info("Hai caricato un report esistente (Modalità Sola Lettura). I calcoli sono già stati effettuati. Vai direttamente alle Dashboards (Tab 3 e 4).")
    else:
        st.info("Per favore, carica i file e seleziona i sample nella Tab 1.")

# --- TAB 3: Dashboard Singola ---
with tab3:
    if st.session_state.processed_data is not None:
        st.header("Analisi Sample Singolo")
        col1, col2 = st.columns([1, 2])
        with col1:
            sample_to_plot = st.selectbox("Seleziona un Sample:", options=st.session_state.selected_samples)
        with col2:
            chart_type_single = st.radio("Scegli la visualizzazione:", ["Dati Elementari (CHNSO)", "Rapporti Atomici", "Composizione 100% & HHV"], horizontal=True, key="radio_single")
        
        if sample_to_plot:
            if "CHNSO" in chart_type_single:
                fig = visualizations.plot_single_sample(st.session_state.processed_data['stats'], sample_to_plot)
            elif "Rapporti" in chart_type_single:
                fig = visualizations.plot_ratios_single(st.session_state.processed_data['stats'], sample_to_plot)
            else:
                fig = visualizations.plot_stacked_single(st.session_state.processed_data['stats'], sample_to_plot)
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Nessun dato processato disponibile.")

# --- TAB 4: Dashboard Confronto ---
with tab4:
    if st.session_state.processed_data is not None:
        st.header("Confronto tra Sample")
        samples_to_compare = st.multiselect("Seleziona i Sample da confrontare:", options=st.session_state.selected_samples, default=st.session_state.selected_samples[:3] if len(st.session_state.selected_samples) >= 3 else st.session_state.selected_samples)
        
        if samples_to_compare:
            chart_type_comp = st.radio("Scegli la visualizzazione:", ["Dati Elementari (CHNSO)", "Rapporti Atomici", "Composizione 100% & HHV"], horizontal=True, key="radio_comp")
            
            if "CHNSO" in chart_type_comp:
                fig_comp = visualizations.plot_comparison(st.session_state.processed_data['stats'], samples_to_compare)
            elif "Rapporti" in chart_type_comp:
                fig_comp = visualizations.plot_ratios_comparison(st.session_state.processed_data['stats'], samples_to_compare)
            else:
                fig_comp = visualizations.plot_stacked_comparison(st.session_state.processed_data['stats'], samples_to_compare)
            
            st.plotly_chart(fig_comp, use_container_width=True)
    else:
        st.info("Nessun dato processato disponibile.")
