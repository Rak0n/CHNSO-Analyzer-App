import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- 1. Grafici Base (CHNSO) ---
def plot_single_sample(stats_df, sample_name):
    row = stats_df[stats_df['Name'] == sample_name].iloc[0]
    elements = ['C', 'O', 'H', 'N', 'S']
    colors = ['#2ca02c', '#1f77b4', '#d62728', '#9467bd', '#ff7f0e']
    
    if 'Moisture_mean' in row and row['Moisture_mean'] > 0:
        elements.append('Moisture')
        colors.append('#17becf')
    if 'Ash_mean' in row and row['Ash_mean'] > 0:
        elements.append('Ash')
        colors.append('#7f7f7f')

    means = [row.get(f'{el}_mean', 0.0) for el in elements]
    stds = [row.get(f'{el}_std', 0.0) for el in elements]
    
    fig = go.Figure(data=[
        go.Bar(x=elements, y=means, marker_color=colors, text=[f"{m:.2f}%" for m in means], textposition='auto', error_y=dict(type='data', array=stds, visible=True))
    ])
    fig.update_layout(title=f"Composizione Elementare: {sample_name}", yaxis_title="Percentuale Massica (%)", xaxis_title="Elemento", template="plotly_white", hovermode="x")
    return fig

def plot_comparison(stats_df, selected_samples):
    df_filtered = stats_df[stats_df['Name'].isin(selected_samples)]
    elements = ['C', 'O', 'H', 'N', 'S']
    
    if 'Moisture_mean' in df_filtered.columns and df_filtered['Moisture_mean'].max() > 0: elements.append('Moisture')
    if 'Ash_mean' in df_filtered.columns and df_filtered['Ash_mean'].max() > 0: elements.append('Ash')
    
    fig = go.Figure()
    for el in elements:
        fig.add_trace(go.Bar(name=el, x=df_filtered['Name'], y=df_filtered[f'{el}_mean'], error_y=dict(type='data', array=df_filtered.get(f'{el}_std', [0]*len(df_filtered)), visible=True)))
        
    fig.update_layout(barmode='group', title="Confronto CHNSO tra Sample", xaxis_title="Sample", yaxis_title="Percentuale Massica (%)", template="plotly_white")
    return fig

# --- 2. Grafici Avanzati (HHV & Ratios) ---
def plot_advanced_single(stats_df, sample_name):
    row = stats_df[stats_df['Name'] == sample_name].iloc[0]
    
    fig = make_subplots(rows=2, cols=2, subplot_titles=("HHV (MJ/Kg)", "Rapporto N/C", "Rapporto H/C", "Rapporto O/C"))
    
    # HHV
    fig.add_trace(go.Bar(x=[sample_name], y=[row['HHV_mean']], marker_color='#e377c2', text=[f"{row['HHV_mean']:.2f}"], textposition='auto', name="HHV"), row=1, col=1)
    # N/C
    fig.add_trace(go.Bar(x=[sample_name], y=[row['NC_mean']], marker_color='#8c564b', text=[f"{row['NC_mean']:.3f}"], textposition='auto', name="N/C"), row=1, col=2)
    # H/C
    fig.add_trace(go.Bar(x=[sample_name], y=[row['HC_mean']], marker_color='#bcbd22', text=[f"{row['HC_mean']:.3f}"], textposition='auto', name="H/C"), row=2, col=1)
    # O/C
    fig.add_trace(go.Bar(x=[sample_name], y=[row['OC_mean']], marker_color='#17becf', text=[f"{row['OC_mean']:.3f}"], textposition='auto', name="O/C"), row=2, col=2)

    fig.update_layout(title_text=f"Parametri Energetici: {sample_name}", template="plotly_white", showlegend=False, height=600)
    return fig

def plot_advanced_comparison(stats_df, selected_samples):
    df = stats_df[stats_df['Name'].isin(selected_samples)]
    
    fig = make_subplots(rows=2, cols=2, subplot_titles=("HHV (MJ/Kg)", "Rapporto N/C", "Rapporto H/C", "Rapporto O/C"))
    
    fig.add_trace(go.Bar(x=df['Name'], y=df['HHV_mean'], marker_color='#e377c2', text=[f"{x:.1f}" for x in df['HHV_mean']], textposition='auto', name="HHV"), row=1, col=1)
    fig.add_trace(go.Bar(x=df['Name'], y=df['NC_mean'], marker_color='#8c564b', name="N/C"), row=1, col=2)
    fig.add_trace(go.Bar(x=df['Name'], y=df['HC_mean'], marker_color='#bcbd22', name="H/C"), row=2, col=1)
    fig.add_trace(go.Bar(x=df['Name'], y=df['OC_mean'], marker_color='#17becf', name="O/C"), row=2, col=2)

    fig.update_layout(title_text="Confronto Parametri Energetici", template="plotly_white", showlegend=False, height=700)
    return fig
