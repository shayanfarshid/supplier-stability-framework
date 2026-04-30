# Supplier Stability Scoring Framework

This application demonstrates a composite supplier stability scoring framework developed for advanced manufacturing supply chains. The framework implements two analytical instruments: (1) the Friction Index System, a multi-variable supplier performance scoring methodology that weights missing parts 8× more heavily than late-arrived parts and amplifies scores for suppliers with poor commitment integrity; and (2) an MD Fault Attribution System for tracking material quality events and supplier fault rates. All data shown is synthetically generated. The framework is designed to be portable to any manufacturing organization's standard ERP data exports.

## Deployment on Streamlit Community Cloud

1. Push the entire `supplier_stability_app/` folder to a GitHub repo, for example `github.com/shayanfarshid/supplier-stability-framework`.
2. Go to [share.streamlit.io](https://share.streamlit.io) and connect GitHub.
3. Select the repository and set `app.py` as the main file.
4. Deploy — the app will be live at a URL similar to `https://[username]-supplier-stability-framework-[hash].streamlit.app`.
5. Link that URL from `sfarshid.me`.

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
