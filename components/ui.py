"""
components/ui.py
Reusable HTML component builders for the Streamlit UI.
Author: Shayan Farshid · sfarshid.me
"""

from config.colors import COLORS


def kpi_card(label: str, value, subtitle: str = "") -> str:
    """Return an HTML KPI card block for st.markdown(unsafe_allow_html=True)."""
    subtitle_html = (
        f'<div style="color:#475569;font-size:11px;margin-top:6px;line-height:1.4;">'
        f'{subtitle}</div>'
        if subtitle else ""
    )
    return f"""
<div style="
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 10px;
    padding: 18px 20px;
    margin: 4px 0;
    min-height: 130px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
">
  <div style="color:#64748b;font-size:11px;font-weight:600;
              text-transform:uppercase;letter-spacing:0.08em;">{label}</div>
  <div style="color:#f1f5f9;font-size:28px;font-weight:700;
              margin-top:6px;letter-spacing:-0.02em;line-height:1.1;">{value}</div>
  {subtitle_html}
</div>"""


def grade_badge(grade: str) -> str:
    """Return an inline HTML badge coloured by performance grade."""
    color = COLORS.get(grade, "#94a3b8")
    return (
        f'<span style="background:{color}18;color:{color};'
        f'border:1px solid {color}33;'
        f'padding:3px 12px;border-radius:9999px;'
        f'font-size:11px;font-weight:600;letter-spacing:0.06em;">'
        f'{grade}</span>'
    )
