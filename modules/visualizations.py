import plotly.graph_objects as go
import plotly.express as px

def plot_single_sample(stats_df, sample_name):
    """
    Crea un istogramma a barre per un singolo sample, con barre di errore (SD).
    """
    # Filtra per il sample scelto
    row = stats_df[stats_df['Name'] == sample_name].iloc[0]
    
    elements = ['C', 'O', 'H', 'N', 'S'] # Sostituito O2 con O
    colors = ['#2ca02c', '#1f77b4', '#d62728', '#9467bd', '#ff7f0e']
    
    # Aggiungiamo dinamicamente Moisture se è > 0 (altrimenti non compare affatto)
    if 'Moisture_mean' in row and row['Moisture_mean'] > 0:
        elements.append('Moisture')
        colors.append('#17becf') # Ciano
        
    # Aggiungiamo dinamicamente Ash se è > 0 (altrimenti non compare affatto)
    if 'Ash_mean' in row and row['Ash_mean'] > 0:
        elements.append('Ash')
        colors.append('#7f7f7f') # Grigio

    # Usiamo .get() per sicurezza nel caso manchi una colonna
    means = [row.get(f'{el}_mean', 0.0) for el in elements]
    stds = [row.get(f'{el}_std', 0.0) for el in elements]
    
    fig = go.Figure(data=[
        go.Bar(
            x=elements,
            y=means,
            marker_color=colors,
            text=[f"{m:.2f}%" for m in means],
            textposition='auto',
            error_y=dict(type='data', array=stds, visible=True, color='black', thickness=1.5)
        )
    ])
    
    fig.update_layout(
        title=f"Composizione Elementare: {sample_name}",
        yaxis_title="Percentuale Massica (%)",
        xaxis_title="Elemento",
        template="plotly_white",
        hovermode="x"
    )
    
    return fig

def plot_comparison(stats_df, selected_samples):
    """
    Crea un Grouped Bar Chart per confrontare più sample.
    """
    df_filtered = stats_df[stats_df['Name'].isin(selected_samples)]
    elements = ['C', 'O', 'H', 'N', 'S'] # Sostituito O2 con O
    
    # Se anche solo UN sample tra quelli selezionati ha Moisture/Ash > 0, lo inseriamo nel confronto
    if 'Moisture_mean' in df_filtered.columns and df_filtered['Moisture_mean'].max() > 0:
        elements.append('Moisture')
    if 'Ash_mean' in df_filtered.columns and df_filtered['Ash_mean'].max() > 0:
        elements.append('Ash')
    
    fig = go.Figure()
    
    # Aggiungi una serie di barre per ogni elemento
    for el in elements:
        fig.add_trace(go.Bar(
            name=el,
            x=df_filtered['Name'],
            y=df_filtered[f'{el}_mean'],
            error_y=dict(type='data', array=df_filtered.get(f'{el}_std', [0]*len(df_filtered)), visible=True),
            text=[f"{val:.1f}%" for val in df_filtered[f'{el}_mean']],
            textposition='none' # Nascosto per evitare sovrapposizioni, visibile in hover
        ))
        
    fig.update_layout(
        barmode='group',
        title="Confronto Elementi tra Sample",
        xaxis_title="Sample",
        yaxis_title="Percentuale Massica (%)",
        template="plotly_white",
        legend_title="Elementi",
        hovermode="closest"
    )
    
    return fig
