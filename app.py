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
    page_icon="S",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown(CSS, unsafe_allow_html=True)

@st.cache_data
def load_data():
    import os
    csv_path = os.path.join(os.path.dirname(__file__), "supplier_order_lines.csv")
    df = pd.read_csv(csv_path)
    for col in ["order_date", "request_date", "commit_date", "received_date"]:
        df[col] = pd.to_datetime(df[col], errors="coerce")
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

def section_header(title, subtitle=""):
    st.markdown(f"## {title}")
    if subtitle:
        st.markdown(f"<p class='section-subtitle'>{subtitle}</p>", unsafe_allow_html=True)

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

    st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)
    section_header("Delivery Performance", "Line-level lateness, open exposure, and average delay across the review period.")

    m1, m2, m3 = st.columns(3)
    with m1:
        st.markdown(kpi_card("Late Arrival Rate", f"{s_metrics['pct_late_arrived']:.1f}%", "Proportion of received lines past commit date"), unsafe_allow_html=True)
    with m2:
        subtitle = "No open-late exposure in current period"
        if s_metrics['count_open_late'] > 0:
            subtitle = "Lines ordered and not yet received past due"
        st.markdown(kpi_card("Open Late Lines", f"{int(s_metrics['count_open_late'])}", subtitle), unsafe_allow_html=True)
    with m3:
        st.markdown(kpi_card("Avg Days Late", f"{s_metrics['avg_days_late']:.1f}", "Mean lateness across delayed lines only"), unsafe_allow_html=True)

    st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)
    section_header("Friction Trend", "Monthly Friction Index trajectory. Values above the threshold indicate elevated delivery risk.")
    monthly = compute_monthly_friction(df, selected)
    fig = monthly_friction_line(monthly, selected)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)
    section_header("Order History", "Full order-line detail. Rows highlighted in red indicate open-late exposure; orange indicates a material discrepancy event.")
    view = sdf[["order_id", "component_category", "component_criticality", "request_date", "commit_date", "received_date",
                "days_late", "has_md_event", "md_fault_type", "is_late_arrived", "is_open_late"]].copy()
    for c in ["request_date", "commit_date", "received_date"]:
        view[c] = pd.to_datetime(view[c]).dt.strftime('%Y-%m-%d')
    st.dataframe(style_order_table(view.head(200)), use_container_width=True, height=500)

    if not s_md.empty:
        st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)
        section_header("Material Discrepancy Fault Attribution", "Quality event volume, supplier fault share, and estimated rework cost for the review period.")
        mdrow = s_md.iloc[0]
        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(kpi_card("Total Quality Events", int(mdrow['open_mdas']), "Material discrepancy events logged in period"), unsafe_allow_html=True)
        c2.markdown(kpi_card("Supplier Fault Count", int(mdrow['supplier_fault_count']), "Events with root cause attributed to supplier"), unsafe_allow_html=True)
        c3.markdown(kpi_card("Supplier Fault Rate", f"{mdrow['pct_supplier_fault']:.1f}%", mdrow['md_flag']), unsafe_allow_html=True)
        c4.markdown(kpi_card("Estimated Rework Cost", fmt_money(mdrow['total_rework_cost_usd']), "Remediation cost on supplier-attributed events"), unsafe_allow_html=True)
        fig_md = md_fault_bar(mdrow['fault_breakdown'])
        if fig_md:
            st.plotly_chart(fig_md, use_container_width=True)
            render_caption("Defect mode distribution across supplier-attributed material discrepancy events.")


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

    section_header("Period Analysis", "Supplier performance summary for the selected period. Use filters in the sidebar to scope by quarter, category, or project.")
    st.dataframe(show, use_container_width=True, height=520)
    csv = show.to_csv(index=False).encode('utf-8')
    st.download_button("Export to CSV", csv, file_name="supplier_period_analysis.csv", mime="text/csv")

    if period_type == "Quarter" and len(selected_quarters) >= 2:
        st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)
        section_header("Quarter-over-Quarter Comparison", "Friction Index by supplier across selected quarters. Persistent elevation indicates a structural performance issue.")
        metrics_by_quarter = {q: compute_friction_metrics(df[(df['quarter'] == q) &
                                (df['component_category'].isin(categories)) &
                                (df['component_criticality'].isin(criticalities)) &
                                (df['project_number'].isin(projects))]) for q in selected_quarters}
        fig = qoq_comparison_bar(metrics_by_quarter)
        st.plotly_chart(fig, use_container_width=True)


def methodology_page():
    section_header("The Problem This Framework Solves",
        "Why standard on-time delivery metrics are insufficient for advanced manufacturing environments.")
    st.write("Most procurement scorecards reduce supplier performance to a single on-time delivery percentage. In routine purchasing environments this is adequate, but it fails in advanced manufacturing — where a single missing critical-path component can halt production, trigger premium freight, and force schedule revisions across dependent work orders.")
    st.write("Standard metrics also collapse structurally different failure modes into the same category. A line arriving three days late is inconvenient. A line that remains undelivered thirty days past due can stop builds, displace labor, and cascade into customer commitments. This framework distinguishes between those outcomes by design.")

    st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)
    section_header("Friction Index — Design Rationale",
        "A composite risk score incorporating lateness frequency, open exposure, commitment integrity, and delay severity.")
    st.write("The Friction Index integrates four performance dimensions: the rate of late-arrived lines, the count of open-late lines still outstanding, the supplier's planning score (a measure of how far commit dates deviate from request dates), and a non-linear severity factor that amplifies scores when the longest delays exceed an operationally significant threshold.")
    st.write("Open-late lines are weighted substantially higher than late-arrived lines, reflecting that an undelivered part creates fundamentally greater operational risk than one that arrived late but closed. The planning score acts as a divisor — suppliers that consistently commit beyond the buyer's need date amplify their own friction score even before a delivery failure occurs.")
    st.write("Scores are volume-weighted, ensuring that a highly problematic supplier managing hundreds of lines is not treated equivalently to one with minimal order activity.")

    st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)
    section_header("Material Discrepancy Fault Attribution",
        "Isolating supplier-attributed quality events from transit and handling noise.")
    st.write("Material discrepancy tracking is most actionable when causality is assigned. This system distinguishes supplier-responsible events from those attributable to transit damage, incoming inspection error, or downstream integration issues — separating genuine supplier quality instability from systemic fulfillment chain noise.")
    st.write("Each event is categorized by defect mode and root-cause owner. When the proportion of supplier-attributed events exceeds fifty percent of the total, the supplier is flagged for structured corrective action review. Rework cost and production time lost are tracked alongside event counts to provide a financial impact dimension.")

    st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)
    section_header("Framework Portability",
        "Designed to operate across ERP environments without custom integration.")
    st.write("The scoring logic requires five standard fields available in any ERP export: Supplier Name, Request Date, Commit Date, Received Date, and a quality event log with fault classification. The framework is ERP-agnostic and has been designed for compatibility with SAP, Oracle, NetSuite, and custom procurement stacks.")

    st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)
    section_header("Data Notice")
    st.write("All data in this application is synthetically generated for demonstration purposes. It does not represent any real organization, supplier, procurement operation, or historical performance record.")


def dashboard_page(df, metrics_df):
    section_header("Portfolio Overview",
        "Delivery performance, commitment integrity, and spend exposure across the full supplier portfolio.")

    total_suppliers = metrics_df['supplier_name'].nunique()
    critical_at_risk = (metrics_df['friction_index'] > 20).sum()
    portfolio_avg = np.average(metrics_df['friction_index'], weights=metrics_df['total_lines_ordered'])
    total_at_risk = metrics_df['at_risk_spend_usd'].sum()

    k1, k2, k3, k4 = st.columns(4)
    k1.markdown(kpi_card("Suppliers Monitored", total_suppliers, "Active suppliers in the synthetic portfolio"), unsafe_allow_html=True)
    k2.markdown(kpi_card("Elevated Risk Suppliers", critical_at_risk, "Friction Index exceeding threshold of 20"), unsafe_allow_html=True)
    k3.markdown(kpi_card("Portfolio Friction Index", f"{portfolio_avg:.2f}", "Volume-weighted composite score across all suppliers"), unsafe_allow_html=True)
    k4.markdown(kpi_card("At-Risk Spend Exposure", fmt_money(total_at_risk), "Spend on open-late and late-arrived order lines"), unsafe_allow_html=True)

    st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)
    section_header("Supplier Friction Ranking",
        "Ranked by Friction Index. Suppliers above the threshold warrant prioritized review and corrective engagement.")
    fig1 = friction_bar_chart(metrics_df)
    st.plotly_chart(fig1, use_container_width=True)

    st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)
    section_header("Risk Distribution",
        "Commitment integrity versus operational friction, and portfolio spend concentration by supplier.")
    c1, c2 = st.columns(2)
    with c1:
        fig2 = scatter_planning_vs_friction(metrics_df)
        st.plotly_chart(fig2, use_container_width=True)
        render_caption("Commitment integrity (x-axis) versus Friction Index (y-axis). Upper-left quadrant: low planning integrity combined with high delivery risk. Bubble size reflects order volume.")
    with c2:
        fig3 = spend_treemap(metrics_df)
        st.plotly_chart(fig3, use_container_width=True)
        render_caption("Portfolio spend distribution by supplier, sized by total order value. Color encodes performance grade. Red blocks represent elevated spend concentration in high-risk relationships.")


def sidebar_intro():
    st.sidebar.markdown("# Supplier Stability Framework")
    st.sidebar.markdown("**A Deep-Tier Risk Analytics Demo**")
    st.sidebar.markdown(
        "<p style='font-size:12px;color:#64748b;line-height:1.6;margin-top:4px;'>"
        "A synthetic demonstration of a field-deployable supplier risk scoring framework. "
        "Evaluates delivery performance, commitment integrity, and material discrepancy attribution "
        "beyond standard on-time metrics."
        "</p>", unsafe_allow_html=True
    )
    st.sidebar.markdown("---")

def main():
    df = load_data()
    metrics_df, md_df = get_metrics(df)

    sidebar_intro()
    page = st.sidebar.radio("Navigation", ["Portfolio Overview", "Supplier Deep-Dive", "Period Analysis", "Methodology"])
    st.sidebar.markdown("---")
    st.sidebar.caption("v1.0 · sfarshid.me · Synthetic Data Only")

    if page == "Portfolio Overview":
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
