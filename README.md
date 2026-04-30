# Supplier Stability Scoring Framework

This application demonstrates a composite supplier stability scoring framework developed for advanced manufacturing supply chains. The framework implements two analytical instruments: (1) the Friction Index System, a multi-variable supplier performance scoring methodology that weights missing parts 8× more heavily than late-arrived parts and amplifies scores for suppliers with poor commitment integrity; and (2) an MD Fault Attribution System for tracking material quality events and supplier fault rates. All data shown is synthetically generated. The framework is designed to be portable to any manufacturing organization's standard ERP data exports.


## Local Run

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Files

- `app.py` — main Streamlit entry point
- `data_generator.py` — deterministic synthetic data generation
- `analytics.py` — Friction Index and MD calculations
- `charts.py` — Plotly visual builders
- `styles.py` — theme, CSS, badges, KPI card helpers
- `requirements.txt` — Python dependencies
