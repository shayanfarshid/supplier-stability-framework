"""
styles.py  —  thin compatibility shim

All style logic now lives in:
  assets/theme.css      → raw CSS injected via st.markdown
  config/colors.py      → COLORS dict and PLOTLY_LAYOUT
  components/ui.py      -> kpi_card() and grade_badge()

This file re-exports everything so app.py imports remain unchanged.
Author: Shayan Farshid · sfarshid.me
"""

import pathlib

from config.colors import COLORS, PLOTLY_LAYOUT          # noqa: F401
from components.ui import kpi_card, grade_badge          # noqa: F401

# Load the external CSS file and wrap it in a <style> tag
_css_path = pathlib.Path(__file__).parent / "assets" / "theme.css"
CSS = f"<style>\n{_css_path.read_text()}\n</style>"
