COLORS = {
    "OUTSTANDING": "#0d9488",
    "EXCELLENT": "#16a34a",
    "ACCEPTABLE": "#d97706",
    "WATCH": "#ea580c",
    "AT RISK": "#dc2626",
    "CRITICAL": "#7f1d1d",
    "bg_primary": "#0f172a",
    "bg_card": "#1e293b",
    "accent": "#0d9488",
    "text_primary": "#f1f5f9",
    "text_muted": "#94a3b8",
    "border": "#334155",
}

PLOTLY_LAYOUT = dict(
    paper_bgcolor="#0f172a",
    plot_bgcolor="#1e293b",
    font=dict(color="#94a3b8", family="Inter, system-ui, sans-serif"),
    xaxis=dict(gridcolor="#334155", linecolor="#334155", zerolinecolor="#334155"),
    yaxis=dict(gridcolor="#334155", linecolor="#334155", zerolinecolor="#334155"),
    margin=dict(l=60, r=30, t=50, b=50),
    legend=dict(bgcolor="#1e293b", bordercolor="#334155"),
)

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', system-ui, sans-serif;
    background-color: #0f172a !important;
    color: #f1f5f9;
}
.stApp { background-color: #0f172a; }

section[data-testid="stSidebar"] {
    background-color: #0d1425 !important;
    border-right: 1px solid #1e293b;
}
section[data-testid="stSidebar"] * { color: #94a3b8 !important; }
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 { color: #f1f5f9 !important; }
section[data-testid="stSidebar"] strong { color: #cbd5e1 !important; }

.stSelectbox > div > div, .stMultiSelect > div > div {
    background-color: #1e293b !important;
    border-color: #334155 !important;
    color: #f1f5f9 !important;
}
.stDataFrame { background-color: #1e293b; }

h1, h2, h3, h4 { color: #f1f5f9 !important; letter-spacing: -0.01em; }
h2 { font-size: 1.4rem !important; font-weight: 600 !important; margin-bottom: 2px !important; }
h3 { font-size: 1.1rem !important; font-weight: 600 !important; }
p { color: #cbd5e1; line-height: 1.7; }
hr { border-color: #1e293b; }

.section-subtitle {
    color: #64748b !important;
    font-size: 13px !important;
    margin-top: -8px !important;
    margin-bottom: 20px !important;
    line-height: 1.5;
}

.section-divider {
    border-top: 1px solid #1e293b;
    margin: 32px 0 24px 0;
}

.stButton > button {
    background-color: #0d9488;
    color: white;
    border: none;
    border-radius: 6px;
    font-weight: 600;
    font-size: 13px;
    padding: 6px 16px;
}
.stButton > button:hover { background-color: #0f766e; }

footer { visibility: hidden; }
.footer-custom {
    position: fixed; bottom: 0; left: 0; right: 0;
    background: #0d1425;
    border-top: 1px solid #1e293b;
    padding: 8px 24px;
    font-size: 11px;
    color: #475569;
    text-align: center;
    z-index: 999;
    letter-spacing: 0.02em;
}
</style>
"""

def kpi_card(label, value, subtitle=""):
    return f"""
<div style="
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 10px;
    padding: 18px 20px;
    margin: 4px 0;
">
  <div style="color:#64748b;font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:0.08em;">{label}</div>
  <div style="color:#f1f5f9;font-size:28px;font-weight:700;margin-top:6px;letter-spacing:-0.02em;line-height:1.1;">{value}</div>
  <div style="color:#475569;font-size:11px;margin-top:6px;line-height:1.4;">{subtitle}</div>
</div>"""

def grade_badge(grade):
    color = COLORS.get(grade, "#94a3b8")
    return (f'<span style="background:{color}18;color:{color};border:1px solid {color}33;' 
            f'padding:3px 12px;border-radius:9999px;font-size:11px;font-weight:600;letter-spacing:0.06em;">'
            f'{grade}</span>')
