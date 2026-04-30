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
    selected = st.sidebar.selectbox("Select Supplier", suppliers)

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
        st.markdown(kpi_card("% Lines Late Arrived", f"{s_metrics['pct_late_arrived']:.1f}%", "Late but eventually received"), unsafe_allow_html=True)
    with m2:
        subtitle = "Open parts beyond commit+4 days"
        if s_metrics['count_open_late'] > 0:
            subtitle = "⚠ Open late exposure present"
        st.markdown(kpi_card("Open Late Parts", f"{int(s_metrics['count_open_late'])}", subtitle), unsafe_allow_html=True)
    with m3:
        st.markdown(kpi_card("Avg Days Late", f"{s_metrics['avg_days_late']:.1f}", "Late-arrived lines only"), unsafe_allow_html=True)

    monthly = compute_monthly_friction(df, selected)
    fig = monthly_friction_line(monthly, selected)
    st.plotly_chart(fig, use_container_width=True)
    render_caption("The monthly series reveals whether friction is trending downward, worsening over time, or oscillating unpredictably.")

    st.markdown("### Order History")
    view = sdf[["order_id", "component_category", "component_criticality", "request_date", "commit_date", "received_date",
                "days_late", "has_md_event", "md_fault_type", "is_late_arrived", "is_open_late"]].copy()
    for c in ["request_date", "commit_date", "received_date"]:
        view[c] = pd.to_datetime(view[c]).dt.strftime('%Y-%m-%d')
    st.dataframe(style_order_table(view.head(200)), use_container_width=True, height=500)

    if not s_md.empty:
        st.markdown("### MD Fault Attribution")
        mdrow = s_md.iloc[0]
        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(kpi_card("Total MDAs", int(mdrow['open_mdas']), "Quality events in period"), unsafe_allow_html=True)
        c2.markdown(kpi_card("Supplier Fault Count", int(mdrow['supplier_fault_count']), "Attributed to supplier"), unsafe_allow_html=True)
        c3.markdown(kpi_card("% Supplier Fault", f"{mdrow['pct_supplier_fault']:.1f}%", mdrow['md_flag']), unsafe_allow_html=True)
        c4.markdown(kpi_card("Total Rework Cost", fmt_money(mdrow['total_rework_cost_usd']), "Supplier-fault events only"), unsafe_allow_html=True)
        fig_md = md_fault_bar(mdrow['fault_breakdown'])
        if fig_md:
            st.plotly_chart(fig_md, use_container_width=True)
            render_caption("The horizontal breakdown shows which defect modes dominate supplier-attributed quality failures.")


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
        'total_spend_usd':'Spend', 'at_risk_spend_usd':'At-Risk Spend', 'open_mdas':'MD Events', 'md_flag':'MD Flag'
    })
    show = summary[['supplier_name','Lines','% Late','Open Late','Planning Score','Friction Index','Grade','Spend','At-Risk Spend','MD Events','MD Flag']].copy()
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
    st.write("Standard procurement scorecards often reduce supplier performance to a single on-time delivery percentage, but that simplification breaks down in advanced manufacturing environments where shortages propagate across constrained production schedules. A supplier that performs well on routine demand can still create major disruption if failures cluster around critical-path components.")
    st.write("Traditional dashboards also collapse very different failure conditions into the same bucket. A part that arrives three days late is inconvenient; a part that remains missing thirty days past due can stop builds, trigger expedites, and force planners to reshuffle labor, capacity, and customer commitments.")
    st.write("The framework shown in this application addresses that deep-tier visibility gap by distinguishing mild delay from severe disruption, and by treating commitment integrity as a performance variable in its own right. In practice, a supplier that consistently promises dates far beyond requested need dates introduces friction before a delivery is even missed.")

    st.markdown("## The Friction Index — Design Rationale")
    st.latex(r"Planning\ Score = \max(0, 1 - (\overline{Commit\ Date - Request\ Date} \times 0.02))")
    st.write("The Planning Score measures commitment integrity. When a supplier repeatedly commits well beyond the requested need date, the score falls, reflecting that the supplier is not truly supporting production timing even if it later ships to its own extended promise date.")
    st.latex(r"Volume\ Weight = (\frac{supplier\_line\_count}{max\_line\_count} \times 0.5) + 0.5")
    st.write("Volume Weight scales operational impact. A problematic supplier with two lines matters less than a problematic supplier feeding hundreds of order lines into the plant, so the framework raises the influence of higher-volume relationships.")
    st.latex(r"Severity\ Factor = 1 + (proportion\ of\ lates\ over\ 20\ days \times 2)")
    st.write("Severity is treated non-linearly because long delays cross operational thresholds. Once lateness stretches beyond a few days, teams often incur premium freight, schedule churn, expediting effort, and elevated management attention.")
    st.latex(r"Friction\ Index = ((\%\ Late\ Arrived + (\%\ Open\ Late \times 8)) / Planning\ Score) \times Volume\ Weight \times Severity\ Factor")
    st.write("The 8× multiplier on open-late lines reflects that a missing part is categorically worse than a part that eventually arrived late. Dividing by Planning Score amplifies delivery failure when it coexists with weak commitment integrity, which is more realistic than simply adding the two effects together.")

    st.markdown("## The MD Fault Attribution System")
    st.write("Material discrepancy tracking becomes far more useful when defect counts are paired with causality. Distinguishing supplier-responsible events from transit, handling, or downstream integration issues lets procurement teams separate true supplier quality instability from noise in the broader fulfillment chain.")
    st.write("The framework therefore tracks event count, supplier-fault share, rework cost, and days lost. The 50 percent flag threshold is intentionally practical: once the majority of quality events are supplier-attributed, the relationship warrants structured corrective action rather than passive monitoring.")

    st.markdown("## Framework Portability")
    st.write("This framework is designed to travel across ERP environments rather than depend on one company’s system architecture. Any organization able to export Supplier Name, Request Date, Commit Date, Received Date, and a quality-event log can operationalize the same scoring logic whether the source platform is SAP, Oracle, NetSuite, or a custom stack.")

    st.markdown("## A Note on Synthetic Data")
    st.write("All data in this application is synthetically generated for demonstration purposes. It does not represent any real organization, supplier, project, procurement operation, or historical performance record.")


def dashboard_page(df, metrics_df):
    st.markdown("## Dashboard Overview")
    total_suppliers = metrics_df['supplier_name'].nunique()
    critical_at_risk = (metrics_df['friction_index'] > 20).sum()
    portfolio_avg = np.average(metrics_df['friction_index'], weights=metrics_df['total_lines_ordered'])
    total_at_risk = metrics_df['at_risk_spend_usd'].sum()

    k1, k2, k3, k4 = st.columns(4)
    k1.markdown(kpi_card("Total Suppliers Monitored", total_suppliers, "Distinct suppliers in synthetic portfolio"), unsafe_allow_html=True)
    k2.markdown(kpi_card("Critical / At-Risk Suppliers", critical_at_risk, "Friction Index greater than 20"), unsafe_allow_html=True)
    k3.markdown(kpi_card("Portfolio Avg Friction Index", f"{portfolio_avg:.2f}", "Weighted by supplier line volume"), unsafe_allow_html=True)
    k4.markdown(kpi_card("Total At-Risk Spend USD", fmt_money(total_at_risk), "Late-arrived and open-late lines"), unsafe_allow_html=True)

    fig1 = friction_bar_chart(metrics_df)
    st.plotly_chart(fig1, use_container_width=True)
    render_caption("Suppliers at the top combine the highest operational friction with the greatest need for intervention priority.")

    c1, c2 = st.columns(2)
    with c1:
        fig2 = scatter_planning_vs_friction(metrics_df)
        st.plotly_chart(fig2, use_container_width=True)
        render_caption("Suppliers in the upper-left quadrant combine low commitment integrity with high friction, making them the highest-priority intervention targets.")
    with c2:
        fig3 = spend_treemap(metrics_df)
        st.plotly_chart(fig3, use_container_width=True)
        render_caption("Larger blocks indicate where supplier instability overlaps with higher dollar exposure across the portfolio.")


def sidebar_intro():
    st.sidebar.markdown("# ⚙️ Supplier Stability Scoring Framework")
    st.sidebar.markdown("### A Deep-Tier Risk Analytics Demo")
    st.sidebar.markdown("This portfolio application demonstrates a field-portable supplier analytics framework using entirely synthetic procurement data. It is designed to show how late delivery risk and material discrepancy causality can be scored beyond standard on-time metrics.")
    st.sidebar.markdown("---")

def main():
    df = load_data()
    metrics_df, md_df = get_metrics(df)

    sidebar_intro()
    page = st.sidebar.radio("Navigation", ["Dashboard Overview", "Supplier Deep-Dive", "Period Analysis", "Methodology"])
    st.sidebar.markdown("---")
    st.sidebar.caption("Synthetic demonstration data — not representative of any real organization.")
    st.sidebar.caption("v1.0 · sfarshid.me · Synthetic Data Only")

    st.markdown("<div style='color:#94a3b8;margin-bottom:10px;'>Synthetic demonstration data — not representative of any real organization.</div>", unsafe_allow_html=True)

    if page == "Dashboard Overview":
        dashboard_page(df, metrics_df)
    elif page == "Supplier Deep-Dive":
        supplier_profile_page(df, metrics_df, md_df)
    elif page == "Period Analysis":
        period_analysis_page(df)
    else:
        methodology_page()

    st.markdown("<div class='footer-custom'>Synthetic demonstration data only. Framework developed by Shayan Farshid. sfarshid.me</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
