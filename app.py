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

st.title("🧪 CHNSO Analyzer & Dashboard")
st.markdown("Analisi automatizzata dei dati elementari, calcolo dell'Ossigeno ed esportazione avanzata.")

# Creazione delle schede (Tabs)
tab1, tab2, tab3, tab4 = st.tabs([
    "📂 1. Caricamento Dati", 
    "⚙️ 2. Calcoli e Umidità/Ceneri", 
    "📊 3. Dashboard Singola", 
    "⚖️ 4. Dashboard Confronto"
])

# --- TAB 1: Caricamento Dati ---
with tab1:
    uploaded_files = st.file_uploader(
        "Trascina qui i tuoi file Excel (.xlsx)", 
        type=['xlsx'], 
        accept_multiple_files=True
    )

    if uploaded_files:
        with st.spinner("Lettura dei file in corso..."):
            # Carica e unisce i file (usa la cache per efficienza)
            df_raw = file_handler.load_excel_files(uploaded_files)
            
            if not df_raw.empty:
                st.session_state.raw_data = df_raw
                st.success("File caricati e uniti con successo!")
                
                all_samples = df_raw['Name'].dropna().unique().tolist()
                
                st.subheader("✅ 1. Selezione Sample")
                st.write("Spunta la casella 'Seleziona' per includere il sample nell'analisi. Le caselle sono inizialmente vuote.")
                
                # INIZIALIZZAZIONE SICURA: previene il salto dello scroll, i doppi click e la perdita di focus
                if 'selection_state' not in st.session_state or st.session_state.get('last_file') != df_raw.shape[0]:
                    st.session_state.selection_state = pd.DataFrame({
                        "Seleziona": [False] * len(all_samples),
                        "Sample": all_samples
                    })
                    st.session_state.last_file = df_raw.shape[0]

                # Tabella 1: Solo Selezione. L'uso di "key" isola il componente ed evita ricaricamenti molesti
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
                
                # Estraiamo i sample che l'utente ha spuntato
                selected_unsorted = edited_selection[edited_selection["Seleziona"]]["Sample"].tolist()
                
                # Tabella 2: Anteprima e Ordinamento (visibile solo se ci sono sample selezionati)
                if selected_unsorted:
                    st.subheader("🔢 2. Anteprima Dati e Ordinamento")
                    st.write("Qui vedi i sample scelti. Modifica il numero nella colonna 'Ordine' e clicca sull'intestazione per riordinare l'export.")
                    
                    # Aggiorniamo la tabella ordine SOLO se l'utente seleziona/deseleziona qualcosa.
                    # Questo previene il fastidioso bug della cancellazione del testo mentre l'utente digita il numero.
                    if 'order_state' not in st.session_state or set(st.session_state.get('last_selected', [])) != set(selected_unsorted):
                        df_unique = pd.DataFrame({"Name": selected_unsorted})
                        df_unique["Ordine"] = range(1, len(selected_unsorted) + 1)
                        
                        # Aggiungiamo l'anteprima (prendiamo la prima riga utile del sample come contesto)
                        preview_cols = [c for c in ['Weight', 'N', 'C', 'H', 'S'] if c in df_raw.columns]
                        df_first_raw = df_raw.drop_duplicates(subset=['Name']).copy()
                        df_order_preview = pd.merge(df_unique, df_first_raw[['Name'] + preview_cols], on='Name', how='left')
                        
                        st.session_state.order_state = df_order_preview
                        st.session_state.last_selected = selected_unsorted
                        
                    # Configurazione colonne: blocchiamo TUTTO tranne la colonna "Ordine"
                    col_configs = {
                        "Ordine": st.column_config.NumberColumn("Ordine", min_value=1, step=1),
                        "Name": st.column_config.TextColumn("Nome Sample", disabled=True)
                    }
                    for col in [c for c in ['Weight', 'N', 'C', 'H', 'S'] if c in df_raw.columns]:
                        col_configs[col] = st.column_config.Column(disabled=True)

                    # Mostriamo la tabella
                    edited_order = st.data_editor(
                        st.session_state.order_state,
                        column_config=col_configs,
                        hide_index=True,
                        use_container_width=True,
                        key="editor_ordine"
                    )
                    
                    # Ordiniamo la lista finale in base al numero inserito dall'utente
                    st.session_state.selected_samples = edited_order.sort_values(by="Ordine")["Name"].tolist()
                else:
                    st.info("👆 Seleziona almeno un sample nella tabella sopra per sbloccare l'anteprima e ordinarli.")
                    st.session_state.selected_samples = []

# --- TAB 2: Calcoli ---
with tab2:
    if st.session_state.raw_data is not None and st.session_state.selected_samples:
        st.header("Impostazioni Ceneri e Umidità")
        
        # Opzione globale per trascurare ceneri/umidità
        ignore_ash_moisture = st.checkbox(
            "🚫 Trascura Ceneri e Umidità per questa sessione (Calcola O2 solo come 100 - CHNS)", 
            value=False
        )
        
        # Griglia di input dinamica
        ash_moisture_data = ui_components.ash_moisture_form(
            st.session_state.selected_samples, 
            ignore_ash_moisture
        )
        
        if st.button("🚀 Esegui Calcoli", type="primary"):
            with st.spinner("Calcolo Medie, Deviazioni Standard e O2%..."):
                # Elaborazione dati
                df_stats, df_pretty, df_means_only = data_processing.process_data(
                    st.session_state.raw_data,
                    st.session_state.selected_samples,
                    ash_moisture_data,
                    ignore_ash_moisture
                )
                
                # Salvataggio in session_state per i grafici
                st.session_state.processed_data = {
                    'stats': df_stats,
                    'pretty': df_pretty,
                    'means': df_means_only,
                    'raw_filtered': st.session_state.raw_data[st.session_state.raw_data['Name'].isin(st.session_state.selected_samples)],
                    'ignore_am': ignore_ash_moisture
                }
                
                st.success("Calcoli completati!")
                st.dataframe(df_pretty, use_container_width=True)
                
                # Pulsante di Download
                excel_buffer = file_handler.create_excel_download(
                    st.session_state.processed_data['raw_filtered'],
                    df_means_only,
                    df_pretty,
                    ignore_ash_moisture
                )
                
                st.download_button(
                    label="📥 Scarica Report Excel",
                    data=excel_buffer,
                    file_name="CHNSO_Report_Analisi.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
    else:
        st.info("Per favore, carica i file e seleziona i sample nella Tab 1.")

# --- TAB 3: Dashboard Singola ---
with tab3:
    if st.session_state.processed_data is not None:
        st.header("Analisi Sample Singolo")
        sample_to_plot = st.selectbox(
            "Seleziona un Sample da visualizzare:", 
            options=st.session_state.selected_samples
        )
        
        if sample_to_plot:
            fig = visualizations.plot_single_sample(
                st.session_state.processed_data['stats'], 
                sample_to_plot
            )
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Esegui i calcoli nella Tab 2 per sbloccare la dashboard.")

# --- TAB 4: Dashboard Confronto ---
with tab4:
    if st.session_state.processed_data is not None:
        st.header("Confronto tra Sample")
        samples_to_compare = st.multiselect(
            "Seleziona i Sample da confrontare:", 
            options=st.session_state.selected_samples,
            default=st.session_state.selected_samples[:3] if len(st.session_state.selected_samples) >= 3 else st.session_state.selected_samples
        )
        
        if samples_to_compare:
            fig_comp = visualizations.plot_comparison(
                st.session_state.processed_data['stats'], 
                samples_to_compare
            )
            st.plotly_chart(fig_comp, use_container_width=True)
    else:
        st.info("Esegui i calcoli nella Tab 2 per sbloccare il confronto.")
