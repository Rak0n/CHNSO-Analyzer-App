import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

# Colori standard per garantire coerenza visiva in tutte le opzioni
COLOR_MAP = {
    'C': '#2ca02c', 'O': '#1f77b4', 'H': '#d62728', 
    'N': '#9467bd', 'S': '#ff7f0e', 'Moisture': '#17becf', 'Ash': '#7f7f7f'
}

# --- 1. Grafici Base (CHNSO) ---
def plot_single_sample(stats_df, sample_name):
    row = stats_df[stats_df['Name'] == sample_name].iloc[0]
    elements = ['C', 'O', 'H', 'N', 'S']
    
    if row.get('Moisture_mean', 0) > 0: elements.append('Moisture')
    if row.get('Ash_mean', 0) > 0: elements.append('Ash')

    means = [row.get(f'{el}_mean', 0.0) for el in elements]
    stds = [row.get(f'{el}_std', 0.0) for el in elements]
    colors = [COLOR_MAP[el] for el in elements]
    
    fig = go.Figure(data=[
        go.Bar(x=elements, y=means, marker_color=colors, text=[f"{m:.2f}%" for m in means], textposition='auto', error_y=dict(type='data', array=stds, visible=True))
    ])
    fig.update_layout(title=f"Composizione Elementare: {sample_name}", yaxis_title="Percentuale Massica (%)", xaxis_title="Elemento", template="plotly_white", hovermode="x")
    return fig

def plot_comparison(stats_df, selected_samples):
    df = stats_df[stats_df['Name'].isin(selected_samples)]
    elements = ['C', 'O', 'H', 'N', 'S']
    
    if df.get('Moisture_mean', pd.Series([0])).max() > 0: elements.append('Moisture')
    if df.get('Ash_mean', pd.Series([0])).max() > 0: elements.append('Ash')
    
    fig = go.Figure()
    for el in elements:
        fig.add_trace(go.Bar(name=el, x=df['Name'], y=df[f'{el}_mean'], marker_color=COLOR_MAP[el], error_y=dict(type='data', array=df.get(f'{el}_std', [0]*len(df)), visible=True)))
        
    fig.update_layout(barmode='group', title="Confronto CHNSO tra Sample", xaxis_title="Sample", yaxis_title="Percentuale Massica (%)", template="plotly_white")
    return fig

# --- 2. Grafici Rapporti Atomici ---
def plot_ratios_single(stats_df, sample_name):
    row = stats_df[stats_df['Name'] == sample_name].iloc[0]
    ratios = ['N/C', 'H/C', 'O/C']
    vals = [row['NC_mean'], row['HC_mean'], row['OC_mean']]
    colors = ['#8c564b', '#bcbd22', '#17becf']
    
    fig = go.Figure(data=[
        go.Bar(x=ratios, y=vals, marker_color=colors, text=[f"{v:.3f}" for v in vals], textposition='auto')
    ])
    fig.update_layout(title=f"Rapporti Atomici: {sample_name}", yaxis_title="Valore Rapporto", xaxis_title="Rapporto", template="plotly_white", hovermode="x")
    return fig

def plot_ratios_comparison(stats_df, selected_samples):
    df = stats_df[stats_df['Name'].isin(selected_samples)]
    
    fig = go.Figure()
    fig.add_trace(go.Bar(name="N/C", x=df['Name'], y=df['NC_mean'], marker_color='#8c564b', text=[f"{v:.3f}" for v in df['NC_mean']], textposition='none'))
    fig.add_trace(go.Bar(name="H/C", x=df['Name'], y=df['HC_mean'], marker_color='#bcbd22', text=[f"{v:.3f}" for v in df['HC_mean']], textposition='none'))
    fig.add_trace(go.Bar(name="O/C", x=df['Name'], y=df['OC_mean'], marker_color='#17becf', text=[f"{v:.3f}" for v in df['OC_mean']], textposition='none'))
    
    fig.update_layout(barmode='group', title="Confronto Rapporti Atomici", xaxis_title="Sample", yaxis_title="Valore Rapporto", template="plotly_white")
    return fig

# --- 3. Grafici Stacked 100% + HHV ---
def plot_stacked_single(stats_df, sample_name):
    # Riusa la logica del confronto passandogli un solo sample
    return plot_stacked_comparison(stats_df, [sample_name])

def plot_stacked_comparison(stats_df, selected_samples):
    df = stats_df[stats_df['Name'].isin(selected_samples)]
    elements = ['C', 'O', 'H', 'N', 'S']
    
    if df.get('Moisture_mean', pd.Series([0])).max() > 0: elements.append('Moisture')
    if df.get('Ash_mean', pd.Series([0])).max() > 0: elements.append('Ash')
    
    # Creiamo un grafico con asse Y secondario (per HHV)
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # 1. Aggiungiamo le barre impilate per gli elementi
    for el in elements:
        fig.add_trace(go.Bar(
            name=el, x=df['Name'], y=df[f'{el}_mean'], 
            marker_color=COLOR_MAP[el],
            hovertemplate=f"{el}: %{{y:.2f}}%<extra></extra>"
        ), secondary_y=False)
        
    # 2. Aggiungiamo la linea con i marcatori per l'HHV sull'asse secondario
    fig.add_trace(go.Scatter(
        name="HHV (MJ/Kg)", x=df['Name'], y=df['HHV_mean'],
        mode='lines+markers', 
        marker=dict(size=12, color='#e377c2', symbol='diamond', line=dict(width=2, color='white')),
        line=dict(width=3, color='#e377c2', dash='dot'),
        hovertemplate="HHV: %{y:.2f} MJ/Kg<extra></extra>"
    ), secondary_y=True)
    
    title = "Composizione 100% & HHV" if len(selected_samples) > 1 else f"Composizione 100% & HHV: {selected_samples[0]}"
    
    fig.update_layout(
        barmode='stack', 
        title=title, 
        xaxis_title="Sample",
        template="plotly_white",
        hovermode="x unified", # Mostra tutti i dati della colonna in un unico tooltip
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    # Assicuriamoci che l'asse percentuale arrivi a ~105 per non tagliare graficamente il 100%
    fig.update_yaxes(title_text="Percentuale Massica (%)", range=[0, 105], secondary_y=False)
    fig.update_yaxes(title_text="HHV (MJ/Kg)", secondary_y=True, showgrid=False)
    
    return fig
