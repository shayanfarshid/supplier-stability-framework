# 🏗️ Supplier Stability Scoring Framework

**A high-fidelity analytical tool for quantifying and optimizing supply chain reliability in advanced manufacturing.**

This framework provides a data-driven approach to evaluating supplier performance by moving beyond just surface-level metrics. It transforms standard ERP data into actionable stability scores using distinct analytical systems to ensure production continuity.

---

## 📊 Core Methodology

The framework utilizes a composite scoring logic to identify performance trends and operational risks before they impact production.

### 1. The Friction Index System
A multi-variable performance scoring methodology designed to prioritize and mitigate line-stop risks.
* **Weighted Urgency:** Strategically weights missing parts $8\times$ more heavily than late arrivals to reflect the actual impact on production throughput.
* **Reliability Amplification:** Dynamically adjusts scores based on **Commitment Integrity**. This ensures suppliers with consistent delivery patterns are recognized over those with volatile or unpredictable schedules.

### 2. MD (Material Discrepancy) Fault Attribution
A precision tracking system for material quality and logistical setbacks.
* **Root Cause Analysis:** Precisely distinguishes between logistical delays and material quality issues to ensure accurate accountability.
* **Performance Accountability:** Tracks specific fault rates to facilitate objective, data-backed discussions during supplier performance reviews.

---

## ✨ Key Features

| Feature | Description |
| :--- | :--- |
| **⚡ Real-Time Visualization** | Built with **Streamlit** and **Plotly** for interactive, high-impact data storytelling and trend analysis. |
| **🧩 ERP Portability** | Designed to be platform-agnostic; maps seamlessly to standard exports regardless of ERP systems- **SAP, Oracle, SYSPRO or Microsoft Dynamics**. |
| **🧪 Deterministic Simulation** | Includes a robust synthetic data generator to demonstrate framework capabilities without exposing proprietary information. |

---

## 🚀 Local Deployment

To run this application locally, ensure you have Python 3.8+ installed and follow these steps:

1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt

This application shows a composite supplier stability scoring framework developed for advanced manufacturing supply chains. The framework implements two analytical tools: (1) the Friction Index System, a multi-variable supplier performance scoring methodology that weights missing parts 8× more heavily than late-arrived parts and amplifies scores for suppliers with poor commitment integrity; and (2) an MD (Material Discrepancy) Fault Attribution System for tracking material quality events and supplier fault rates. All data shown is synthetically generated. The framework is designed to be portable to any manufacturing organization's standard ERP data exports.


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
