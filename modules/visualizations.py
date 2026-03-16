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

# --- 2. Diagramma di Van Krevelen (Rapporti Atomici) ---
def plot_ratios_single(stats_df, sample_name):
    row = stats_df[stats_df['Name'] == sample_name].iloc[0]

    fig = make_subplots(rows=1, cols=2, subplot_titles=("Van Krevelen: H/C vs O/C", "Van Krevelen: H/C vs N/C"))

    # Plot 1: O/C vs H/C
    fig.add_trace(go.Scatter(
        x=[row['OC_mean']], y=[row['HC_mean']],
        mode='markers+text',
        marker=dict(size=14, color='#1f77b4', line=dict(width=2, color='white')),
        text=[sample_name], textposition="top center",
        hovertemplate="<b>%{text}</b><br>O/C: %{x:.3f}<br>H/C: %{y:.3f}<extra></extra>",
        name="O/C vs H/C"
    ), row=1, col=1)

    # Plot 2: N/C vs H/C
    fig.add_trace(go.Scatter(
        x=[row['NC_mean']], y=[row['HC_mean']],
        mode='markers+text',
        marker=dict(size=14, color='#9467bd', line=dict(width=2, color='white')),
        text=[sample_name], textposition="top center",
        hovertemplate="<b>%{text}</b><br>N/C: %{x:.3f}<br>H/C: %{y:.3f}<extra></extra>",
        name="N/C vs H/C"
    ), row=1, col=2)

    fig.update_layout(title=f"Diagrammi di Van Krevelen: {sample_name}", template="plotly_white", showlegend=False, height=500)
    fig.update_xaxes(title_text="Rapporto O/C", row=1, col=1)
    fig.update_yaxes(title_text="Rapporto H/C", row=1, col=1)
    fig.update_xaxes(title_text="Rapporto N/C", row=1, col=2)
    fig.update_yaxes(title_text="Rapporto H/C", row=1, col=2)
    
    return fig

def plot_ratios_comparison(stats_df, selected_samples):
    df = stats_df[stats_df['Name'].isin(selected_samples)].copy()
    
    # Ordiniamo rigidamente il DataFrame affinché la linea colleghi i punti nel tuo ordine scelto
    df['__sort'] = pd.Categorical(df['Name'], categories=selected_samples, ordered=True)
    df = df.sort_values('__sort')

    fig = make_subplots(rows=1, cols=2, subplot_titles=("Van Krevelen: H/C vs O/C", "Van Krevelen: H/C vs N/C"))

    # Plot 1: O/C vs H/C (Linee + Marker)
    fig.add_trace(go.Scatter(
        x=df['OC_mean'], y=df['HC_mean'],
        mode='lines+markers+text',
        marker=dict(size=12, color='#1f77b4', line=dict(width=2, color='white')),
        line=dict(width=3, color='#1f77b4', dash='dot'),
        text=df['Name'], textposition="top center",
        hovertemplate="<b>%{text}</b><br>O/C: %{x:.3f}<br>H/C: %{y:.3f}<extra></extra>",
        name="O/C vs H/C"
    ), row=1, col=1)

    # Plot 2: N/C vs H/C (Linee + Marker)
    fig.add_trace(go.Scatter(
        x=df['NC_mean'], y=df['HC_mean'],
        mode='lines+markers+text',
        marker=dict(size=12, color='#9467bd', line=dict(width=2, color='white')),
        line=dict(width=3, color='#9467bd', dash='dot'),
        text=df['Name'], textposition="top center",
        hovertemplate="<b>%{text}</b><br>N/C: %{x:.3f}<br>H/C: %{y:.3f}<extra></extra>",
        name="N/C vs H/C"
    ), row=1, col=2)

    fig.update_layout(
        title="Confronto Van Krevelen (Percorso Evolutivo / Upgrading)", 
        template="plotly_white", showlegend=False, height=600, 
        margin=dict(t=80) # Diamo margine in alto per le etichette di testo
    )
    fig.update_xaxes(title_text="Rapporto O/C", row=1, col=1)
    fig.update_yaxes(title_text="Rapporto H/C", row=1, col=1)
    fig.update_xaxes(title_text="Rapporto N/C", row=1, col=2)
    fig.update_yaxes(title_text="Rapporto H/C", row=1, col=2)
    
    return fig

# --- 3. Grafici Stacked 100% + HHV ---
def plot_stacked_single(stats_df, sample_name):
    return plot_stacked_comparison(stats_df, [sample_name])

def plot_stacked_comparison(stats_df, selected_samples):
    df = stats_df[stats_df['Name'].isin(selected_samples)]
    elements = ['C', 'O', 'H', 'N', 'S']
    
    if df.get('Moisture_mean', pd.Series([0])).max() > 0: elements.append('Moisture')
    if df.get('Ash_mean', pd.Series([0])).max() > 0: elements.append('Ash')
    
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    for el in elements:
        fig.add_trace(go.Bar(
            name=el, x=df['Name'], y=df[f'{el}_mean'], 
            marker_color=COLOR_MAP[el],
            hovertemplate=f"{el}: %{{y:.2f}}%<extra></extra>"
        ), secondary_y=False)
        
    fig.add_trace(go.Scatter(
        name="HHV (MJ/Kg)", x=df['Name'], y=df['HHV_mean'],
        mode='lines+markers', 
        marker=dict(size=12, color='#e377c2', symbol='diamond', line=dict(width=2, color='white')),
        line=dict(width=3, color='#e377c2', dash='dot'),
        hovertemplate="HHV: %{y:.2f} MJ/Kg<extra></extra>"
    ), secondary_y=True)
    
    title = "Composizione 100% & HHV" if len(selected_samples) > 1 else f"Composizione 100% & HHV: {selected_samples[0]}"
    
    fig.update_layout(
        barmode='stack', title=title, xaxis_title="Sample", template="plotly_white",
        hovermode="x unified", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    fig.update_yaxes(title_text="Percentuale Massica (%)", range=[0, 105], secondary_y=False)
    fig.update_yaxes(title_text="HHV (MJ/Kg)", secondary_y=True, showgrid=False)
    
    return fig
