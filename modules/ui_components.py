import streamlit as st
import pandas as pd

def ash_moisture_form(selected_samples, ignore):
    """
    Crea una tabella editabile per inserire Umidità e Ceneri.
    Restituisce un dizionario: { 'Nome_Sample': {'Umidità': val, 'Ceneri': val} }
    """
    if ignore:
        st.info("Opzione 'Trascura' attiva. Umidità e Ceneri non verranno sottratti dal calcolo dell'O2 e non compariranno nell'export.")
        return {}
        
    st.write("Inserisci i valori % (lascia 0 se non disponibili, verranno usati come zero nei calcoli):")
    
    # Crea un DataFrame di partenza per l'editor
    df_input = pd.DataFrame({
        "Sample": selected_samples,
        "Umidità (%)": [0.0] * len(selected_samples),
        "Ceneri (%)": [0.0] * len(selected_samples)
    })
    
    # Usa st.data_editor per una griglia simile ad Excel
    edited_df = st.data_editor(
        df_input,
        hide_index=True,
        disabled=["Sample"], # Evita che l'utente cambi il nome del sample
        use_container_width=True
    )
    
    # Converte il DataFrame modificato in un dizionario utile al backend
    result_dict = {}
    for _, row in edited_df.iterrows():
        result_dict[row["Sample"]] = {
            'Umidità': row["Umidità (%)"],
            'Ceneri': row["Ceneri (%)"]
        }
        
    return result_dict
