"""
config/colors.py
Centralised color tokens and Plotly layout defaults.
Author: Shayan Farshid · sfarshid.me
"""

COLORS = {
    "OUTSTANDING": "#0d9488",
    "EXCELLENT":   "#16a34a",
    "ACCEPTABLE":  "#d97706",
    "WATCH":       "#ea580c",
    "AT RISK":     "#dc2626",
    "CRITICAL":    "#7f1d1d",
    # Surface / UI
    "bg_primary":  "#0f172a",
    "bg_card":     "#1e293b",
    "accent":      "#0d9488",
    "text_primary": "#f1f5f9",
    "text_muted":  "#94a3b8",
    "border":      "#334155",
}

PLOTLY_LAYOUT = dict(
    paper_bgcolor="#0f172a",
    plot_bgcolor="#1e293b",
    font=dict(color="#94a3b8", family="Inter, system-ui, sans-serif"),
    xaxis=dict(
        gridcolor="#334155",
        linecolor="#334155",
        zerolinecolor="#334155",
    ),
    yaxis=dict(
        gridcolor="#334155",
        linecolor="#334155",
        zerolinecolor="#334155",
    ),
    margin=dict(l=60, r=30, t=50, b=50),
    legend=dict(bgcolor="#1e293b", bordercolor="#334155"),
)
