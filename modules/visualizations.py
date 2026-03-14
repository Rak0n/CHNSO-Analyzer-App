import plotly.graph_objects as go
import plotly.express as px

def plot_single_sample(stats_df, sample_name):
    """
    Crea un istogramma a barre per un singolo sample, con barre di errore (SD).
    """
    # Filtra per il sample scelto
    row = stats_df[stats_df['Name'] == sample_name].iloc[0]
    
    elements = ['C', 'O2', 'H', 'N', 'S'] # Ordine logico e decrescente (generalmente)
    means = [row[f'{el}_mean'] for el in elements]
    stds = [row[f'{el}_std'] for el in elements]
    
    # Palette colori scientifica
    colors = ['#2ca02c', '#1f77b4', '#d62728', '#9467bd', '#ff7f0e']
    
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
    elements = ['C', 'O2', 'H', 'N', 'S']
    
    fig = go.Figure()
    
    # Aggiungi una serie di barre per ogni elemento
    for el in elements:
        fig.add_trace(go.Bar(
            name=el,
            x=df_filtered['Name'],
            y=df_filtered[f'{el}_mean'],
            error_y=dict(type='data', array=df_filtered[f'{el}_std'], visible=True),
            text=[f"{val:.1f}%" for val in df_filtered[f'{el}_mean']],
            textposition='none' # Nascosto per evitare sovrapposizioni, visibile in hover
        ))
        
    fig.update_layout(
        barmode='group',
        title="Confronto Elementi tra Sample (CHNSO)",
        xaxis_title="Sample",
        yaxis_title="Percentuale Massica (%)",
        template="plotly_white",
        legend_title="Elementi",
        hovermode="closest"
    )
    
    return fig
