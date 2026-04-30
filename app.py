import streamlit as st
import pandas as pd
import numpy as np
from io import StringIO

from data_generator import generate_dataset
from analytics import compute_friction_metrics, compute_md_metrics, compute_monthly_friction
from charts import (
    friction_bar_chart, scatter_planning_vs_friction, spend_treemap,
    monthly_friction_line, md_fault_bar, qoq_comparison_bar
)
from styles import CSS, COLORS, kpi_card, grade_badge

st.set_page_config(
    page_title="Supplier Stability Framework | S. Farshid",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown(CSS, unsafe_allow_html=True)

@st.cache_data
def load_data():
    df = generate_dataset(seed=42, n_rows=500)
    for col in ["order_date", "request_date", "commit_date", "received_date"]:
        df[col] = pd.to_datetime(df[col])
    return df

@st.cache_data
def get_metrics(df):
    fr = compute_friction_metrics(df)
    md = compute_md_metrics(df)
    return fr, md

def fmt_money(v):
    if v >= 1_000_000:
        return f"${v/1_000_000:.1f}M"
    if v >= 1_000:
        return f"${v/1_000:.1f}K"
    return f"${v:,.0f}"

def render_caption(text):
    st.caption(text)

def grade_html(grade):
    return grade_badge(grade)

def style_order_table(df):
    def row_color(row):
        if row["is_open_late"]:
            return ['background-color: rgba(220,38,38,0.20)'] * len(row)
        if row["has_md_event"]:
            return ['background-color: rgba(234,88,12,0.18)'] * len(row)
        if row["is_late_arrived"]:
            return ['background-color: rgba(217,119,6,0.18)'] * len(row)
        return ['background-color: rgba(22,163,74,0.10)'] * len(row)
    return df.style.apply(row_color, axis=1)

def supplier_profile_page(df, metrics_df, md_df):
    suppliers = sorted(df["supplier_name"].unique())
    st.sidebar.markdown("### 🔍 Select a Supplier")
    selected = st.sidebar.selectbox("", suppliers)

    s_metrics = metrics_df[metrics_df["supplier_name"] == selected].iloc[0]
    s_md = md_df[md_df["supplier_name"] == selected] if not md_df.empty else pd.DataFrame()
    sdf = df[df["supplier_name"] == selected].sort_values("order_date", ascending=False).copy()

    c1, c2 = st.columns([4, 1.4])
    with c1:
        st.markdown(f"## {selected}", unsafe_allow_html=True)
        st.markdown(grade_html(s_metrics['grade']), unsafe_allow_html=True)
        st.markdown(
            f"<div style='margin-top:12px;color:#cbd5e1;'>"
            f"<b>Friction Index:</b> {s_metrics['friction_index']:.2f} &nbsp;&nbsp;|&nbsp;&nbsp; "
            f"<b>Planning Score:</b> {s_metrics['planning_score']:.2f}</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<div style='margin-top:8px;color:#94a3b8;'>Total Lines Ordered: {int(s_metrics['total_lines_ordered'])} &nbsp;&nbsp;|&nbsp;&nbsp; "
            f"Total Spend: {fmt_money(s_metrics['total_spend_usd'])} &nbsp;&nbsp;|&nbsp;&nbsp; "
            f"At-Risk Spend: {fmt_money(s_metrics['at_risk_spend_usd'])}</div>",
            unsafe_allow_html=True,
        )

    m1, m2, m3 = st.columns(3)
    with m1:
        st.markdown(kpi_card("% Lines Late Arrived", f"{s_metrics['pct_late_arrived']:.1f}%", "Lower is better — 0% = perfect"), unsafe_allow_html=True)
    with m2:
        subtitle = "All clear — no overdue open orders"
        if s_metrics['count_open_late'] > 0:
            subtitle = "⚠ Parts ordered but still not received"
        st.markdown(kpi_card("Open Late Parts", f"{int(s_metrics['count_open_late'])}", subtitle), unsafe_allow_html=True)
    with m3:
        st.markdown(kpi_card("Avg Days Late", f"{s_metrics['avg_days_late']:.1f}", "Lower is better — 0 = always on time"), unsafe_allow_html=True)

    monthly = compute_monthly_friction(df, selected)
    fig = monthly_friction_line(monthly, selected)
    st.plotly_chart(fig, use_container_width=True)
    render_caption("📈 Red dashed line = warning threshold. Spikes above it = trouble. Flat near zero = this supplier is solid.")

    st.markdown("### Order History")
    view = sdf[["order_id", "component_category", "component_criticality", "request_date", "commit_date", "received_date",
                "days_late", "has_md_event", "md_fault_type", "is_late_arrived", "is_open_late"]].copy()
    for c in ["request_date", "commit_date", "received_date"]:
        view[c] = pd.to_datetime(view[c]).dt.strftime('%Y-%m-%d')
    st.dataframe(style_order_table(view.head(200)), use_container_width=True, height=500)

    if not s_md.empty:
        st.markdown("### Material Discrepancy Fault Attribution")
        mdrow = s_md.iloc[0]
        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(kpi_card("Total Quality Events", int(mdrow['open_mdas']), "Material discrepancy events logged"), unsafe_allow_html=True)
        c2.markdown(kpi_card("Supplier Fault Count", int(mdrow['supplier_fault_count']), "Events attributed to supplier"), unsafe_allow_html=True)
        c3.markdown(kpi_card("% Supplier Fault", f"{mdrow['pct_supplier_fault']:.1f}%", mdrow['md_flag']), unsafe_allow_html=True)
        c4.markdown(kpi_card("Total Rework Cost", fmt_money(mdrow['total_rework_cost_usd']), "Cost of fixing supplier-caused defects"), unsafe_allow_html=True)
        fig_md = md_fault_bar(mdrow['fault_breakdown'])
        if fig_md:
            st.plotly_chart(fig_md, use_container_width=True)
            render_caption("The horizontal breakdown shows which defect types dominate supplier-caused quality failures.")


def period_analysis_page(df):
    st.sidebar.markdown("---")
    period_type = st.sidebar.radio("Period Type", ["Quarter", "Custom Date Range"])
    categories = st.sidebar.multiselect("Component Category", sorted(df['component_category'].unique()), default=sorted(df['component_category'].unique()))
    criticalities = st.sidebar.multiselect("Component Criticality", sorted(df['component_criticality'].unique()), default=sorted(df['component_criticality'].unique()))
    projects = st.sidebar.multiselect("Project Number", sorted(df['project_number'].unique()), default=sorted(df['project_number'].unique()))

    if period_type == "Quarter":
        quarters = sorted(df['quarter'].unique())
        selected_quarters = st.sidebar.multiselect("Select Quarter(s)", quarters, default=[quarters[-1]])
        filtered = df[df['quarter'].isin(selected_quarters)]
    else:
        d1, d2 = st.sidebar.date_input("Date Range", [df['order_date'].min().date(), df['order_date'].max().date()])
        filtered = df[(df['order_date'].dt.date >= d1) & (df['order_date'].dt.date <= d2)]
        selected_quarters = []

    filtered = filtered[filtered['component_category'].isin(categories)]
    filtered = filtered[filtered['component_criticality'].isin(criticalities)]
    filtered = filtered[filtered['project_number'].isin(projects)]

    fr = compute_friction_metrics(filtered)
    md = compute_md_metrics(filtered)
    summary = fr.merge(md[['supplier_name', 'open_mdas', 'md_flag']] if not md.empty else pd.DataFrame(columns=['supplier_name','open_mdas','md_flag']),
                       on='supplier_name', how='left')
    summary['open_mdas'] = summary['open_mdas'].fillna(0).astype(int)
    summary['md_flag'] = summary['md_flag'].fillna('✅ PASS')
    summary = summary.rename(columns={
        'total_lines_ordered':'Lines', 'pct_late_arrived':'% Late', 'count_open_late':'Open Late',
        'planning_score':'Planning Score', 'friction_index':'Friction Index', 'grade':'Grade',
        'total_spend_usd':'Spend', 'at_risk_spend_usd':'At-Risk Spend', 'open_mdas':'Discrepancy Events', 'md_flag':'Quality Flag'
    })
    show = summary[['supplier_name','Lines','% Late','Open Late','Planning Score','Friction Index','Grade','Spend','At-Risk Spend','Discrepancy Events','Quality Flag']].copy()
    show = show.rename(columns={'supplier_name':'Supplier'})

    st.markdown("## Period Analysis")
    st.dataframe(show, use_container_width=True, height=520)
    csv = show.to_csv(index=False).encode('utf-8')
    st.download_button("Export summary to CSV", csv, file_name="supplier_period_analysis.csv", mime="text/csv")

    if period_type == "Quarter" and len(selected_quarters) >= 2:
        metrics_by_quarter = {q: compute_friction_metrics(df[(df['quarter'] == q) &
                                (df['component_category'].isin(categories)) &
                                (df['component_criticality'].isin(criticalities)) &
                                (df['project_number'].isin(projects))]) for q in selected_quarters}
        fig = qoq_comparison_bar(metrics_by_quarter)
        st.plotly_chart(fig, use_container_width=True)
        render_caption("Comparing quarters side by side reveals whether supplier friction is persistent, cyclical, or emerging in new periods.")


def methodology_page():
    st.markdown("## The Problem This Framework Solves")
    st.write("Most procurement dashboards reduce a supplier to a single on-time delivery percentage. That works fine for routine purchasing, but it breaks down fast in advanced manufacturing — where one missing critical part can stop an entire production line.")
    st.write("A supplier can be 'on-time' 95% of the time and still cause serious damage if those failures keep hitting the same high-stakes components. And there's a big difference between a part that showed up 3 days late and a part that still hasn't arrived 30 days after it was due.")
    st.write("This framework was built to close that gap — distinguishing nuisance delays from genuine supply risk, and tracking whether a supplier's promises are even realistic in the first place.")

    st.markdown("## How the Friction Index Works")
    st.write("The Friction Index is a composite score that combines four things: how often a supplier is late, how many parts are still missing entirely, how realistic their delivery promises are, and how severe the worst delays tend to be.")
    st.write("Missing parts are weighted much more heavily than parts that arrived late — because a part that hasn't arrived at all can stop production, while a part that arrived a few days late usually just causes rescheduling. Lower scores are better. Zero means a supplier has had no late activity at all.")
    st.write("The score is also amplified when a supplier consistently promises delivery dates that are far beyond what the buyer needs — because unrealistic promising combined with late delivery compounds the damage.")

    st.markdown("## Material Discrepancy Fault Attribution")
    st.write("When a part arrives with a quality problem — wrong dimensions, damaged, or wrong part entirely — it matters a lot whether that was the supplier's fault or something that happened in transit or handling downstream.")
    st.write("This system tracks each quality event and records who was responsible. Once more than half of a supplier's quality events are their fault, the system flags them for corrective action. It also tracks the total rework cost and production time lost, so you can see the financial impact, not just the event count.")

    st.markdown("## Framework Portability")
    st.write("This scoring system works with any standard ERP data export — SAP, Oracle, NetSuite, or custom systems. As long as you have five fields — Supplier Name, Request Date, Commit Date, Received Date, and a quality event log — you can run this framework on your own data.")

    st.markdown("## About This Demo")
    st.write("All supplier names, order data, and performance numbers shown here are entirely synthetic and randomly generated. They don't represent any real company, supplier relationship, or procurement history.")


def dashboard_page(df, metrics_df):
    st.markdown("## Dashboard Overview")
    total_suppliers = metrics_df['supplier_name'].nunique()
    critical_at_risk = (metrics_df['friction_index'] > 20).sum()
    portfolio_avg = np.average(metrics_df['friction_index'], weights=metrics_df['total_lines_ordered'])
    total_at_risk = metrics_df['at_risk_spend_usd'].sum()

    k1, k2, k3, k4 = st.columns(4)
    k1.markdown(kpi_card("Total Suppliers Monitored", total_suppliers, "Suppliers tracked in this portfolio"), unsafe_allow_html=True)
    k2.markdown(kpi_card("Critical / At-Risk Suppliers", critical_at_risk, "⚠️ These need your attention now"), unsafe_allow_html=True)
    k3.markdown(kpi_card("Portfolio Avg Friction Index", f"{portfolio_avg:.2f}", "Lower is better — 0 is perfect"), unsafe_allow_html=True)
    k4.markdown(kpi_card("Total At-Risk Spend USD", fmt_money(total_at_risk), "$ tied to delayed or missing parts"), unsafe_allow_html=True)

    fig1 = friction_bar_chart(metrics_df)
    st.plotly_chart(fig1, use_container_width=True)
    render_caption("📊 Longer bar = more friction. Shorter = healthier supplier. Anything red or dark-red needs action soon.")

    c1, c2 = st.columns(2)
    with c1:
        fig2 = scatter_planning_vs_friction(metrics_df)
        st.plotly_chart(fig2, use_container_width=True)
        render_caption("📍 Upper-left is the danger zone — suppliers who over-promise AND under-deliver. Each dot's size shows how many orders they handle.")
    with c2:
        fig3 = spend_treemap(metrics_df)
        st.plotly_chart(fig3, use_container_width=True)
        render_caption("💰 Bigger block = more $ spent with that supplier. Red/dark blocks are risky suppliers eating a large share of your budget.")


def sidebar_intro():
    st.sidebar.markdown("# ⚙️ Supplier Stability Scoring Framework")
    st.sidebar.markdown("### A Deep-Tier Risk Analytics Demo")
    st.sidebar.markdown("Track which suppliers are causing headaches — late deliveries, missing parts, and quality issues — all in one place. Built as a demo with fake data, but the scoring logic works on any real ERP export.")
    st.sidebar.markdown("---")

def main():
    df = load_data()
    metrics_df, md_df = get_metrics(df)

    sidebar_intro()
    page = st.sidebar.radio("Navigation", ["Dashboard Overview", "Supplier Deep-Dive", "Period Analysis", "Methodology"])
    st.sidebar.markdown("---")
    st.sidebar.caption("v1.0 · sfarshid.me · Synthetic Data Only")

    if page == "Dashboard Overview":
        dashboard_page(df, metrics_df)
    elif page == "Supplier Deep-Dive":
        supplier_profile_page(df, metrics_df, md_df)
    elif page == "Period Analysis":
        period_analysis_page(df)
    else:
        methodology_page()

    st.markdown("<div class='footer-custom'>Synthetic demonstration data only. Framework developed by Shayan F. · sfarshid.me</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
