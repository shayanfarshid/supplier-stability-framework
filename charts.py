import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from styles import COLORS, PLOTLY_LAYOUT


def _apply_layout(fig, title="", height=None):
    updates = dict(**PLOTLY_LAYOUT, title=dict(text=title, font=dict(color="#f1f5f9", size=14), x=0))
    if height:
        updates["height"] = height
    fig.update_layout(**updates)
    return fig


def friction_bar_chart(metrics_df):
    df = metrics_df.sort_values("friction_index", ascending=True).copy()
    df["color"] = df["grade"].map(COLORS)
    df["label"] = df.apply(
        lambda r: f"  {r['grade']}  |  FI: {r['friction_index']:.2f}", axis=1)

    fig = go.Figure(go.Bar(
        x=df["friction_index"],
        y=df["supplier_name"],
        orientation="h",
        marker_color=df["color"],
        text=df["grade"],
        textposition="inside",
        textfont=dict(color="white", size=10),
        customdata=np.stack([df["planning_score"], df["total_lines_ordered"], df["friction_index"]], axis=-1),
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Friction Index: %{customdata[2]:.3f}<br>"
            "Planning Score: %{customdata[0]:.3f}<br>"
            "Lines Ordered: %{customdata[1]}<extra></extra>"
        )
    ))
    fig.update_xaxis(title="Friction Index →")
    fig.update_yaxis(tickfont=dict(size=9))
    _apply_layout(fig, "Supplier Friction Index Ranking", height=max(500, len(df) * 20))
    return fig


def scatter_planning_vs_friction(metrics_df):
    df = metrics_df.copy()
    df["color"] = df["grade"].map(COLORS)
    df["size_scaled"] = np.sqrt(df["total_lines_ordered"]) * 4

    fig = go.Figure()

    # High Risk Zone shading
    fig.add_shape(type="rect", x0=0, x1=0.5, y0=1, y1=df["friction_index"].max() * 1.2,
                  fillcolor="rgba(220,38,38,0.08)", line=dict(color="rgba(220,38,38,0.25)", width=1))
    fig.add_annotation(x=0.25, y=df["friction_index"].max() * 0.9,
                       text="⚠ High Risk Zone<br>Low Commitment Integrity + High Friction",
                       showarrow=False, font=dict(color="#dc2626", size=10),
                       align="center", bgcolor="rgba(15,23,42,0.7)", bordercolor="#dc2626",
                       borderwidth=1, borderpad=6)

    for grade in ["OUTSTANDING", "EXCELLENT", "ACCEPTABLE", "WATCH", "AT RISK", "CRITICAL"]:
        sub = df[df["grade"] == grade]
        if sub.empty:
            continue
        fig.add_trace(go.Scatter(
            x=sub["planning_score"], y=sub["friction_index"],
            mode="markers", name=grade,
            marker=dict(color=COLORS[grade], size=sub["size_scaled"].clip(6, 30),
                        line=dict(color="white", width=0.4), opacity=0.85),
            customdata=np.stack([sub["supplier_name"], sub["friction_index"],
                                  sub["planning_score"], sub["total_lines_ordered"]], axis=-1),
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "Friction Index: %{customdata[1]:.3f}<br>"
                "Planning Score: %{customdata[2]:.3f}<br>"
                "Lines: %{customdata[3]}<extra></extra>"
            )
        ))

    fig.update_xaxis(title="Planning Score (1.0 = perfect commitment integrity)", range=[0, 1.05])
    fig.update_yaxis(title="Friction Index (log scale)", type="log")
    fig.add_vline(x=0.5, line_dash="dot", line_color="#475569", annotation_text="Commitment boundary",
                  annotation_font_color="#64748b", annotation_font_size=10)
    _apply_layout(fig, "Planning Score vs. Friction Index", height=480)
    return fig


def spend_treemap(metrics_df):
    df = metrics_df.copy()
    df["color_val"] = df["grade"].map({g: i for i, g in enumerate(
        ["OUTSTANDING", "EXCELLENT", "ACCEPTABLE", "WATCH", "AT RISK", "CRITICAL"])})
    df["label"] = df["supplier_name"] + "<br>" + df["grade"]

    fig = px.treemap(
        df, path=[px.Constant("All Suppliers"), "grade", "supplier_name"],
        values="total_spend_usd",
        color="grade",
        color_discrete_map=COLORS,
        hover_data={"total_spend_usd": ":,.0f", "friction_index": ":.2f"},
        custom_data=["supplier_name", "grade", "friction_index"],
    )
    fig.update_traces(
        texttemplate="<b>%{label}</b><br>$%{value:,.0f}",
        hovertemplate="<b>%{customdata[0]}</b><br>Grade: %{customdata[1]}<br>"
                      "FI: %{customdata[2]:.2f}<br>Spend: $%{value:,.0f}<extra></extra>",
        textfont=dict(size=10)
    )
    _apply_layout(fig, "Portfolio Spend at Risk by Supplier Grade", height=480)
    return fig


def monthly_friction_line(monthly_df, supplier_name):
    fig = go.Figure()
    fig.add_hline(y=20, line_dash="dash", line_color="#dc2626",
                  annotation_text="AT RISK threshold (FI = 20)",
                  annotation_font_color="#dc2626", annotation_font_size=10,
                  annotation_position="top left")
    fig.add_trace(go.Scatter(
        x=monthly_df["month"], y=monthly_df["friction_index"],
        mode="lines+markers+text",
        line=dict(color="#0d9488", width=2),
        marker=dict(size=6, color="#0d9488"),
        fill="tozeroy", fillcolor="rgba(13,148,136,0.08)",
        hovertemplate="Month: %{x}<br>Friction Index: %{y:.3f}<extra></extra>"
    ))
    fig.update_xaxis(title="Month", tickangle=-30)
    fig.update_yaxis(title="Friction Index")
    _apply_layout(fig, f"Monthly Friction Index — {supplier_name}", height=350)
    return fig


def md_fault_bar(fault_breakdown: dict):
    if not fault_breakdown:
        return None
    labels = list(fault_breakdown.keys())
    values = list(fault_breakdown.values())
    colors = ["#0d9488", "#16a34a", "#d97706", "#ea580c", "#dc2626", "#7f1d1d"]
    fig = go.Figure(go.Bar(
        x=values, y=labels, orientation="h",
        marker_color=colors[:len(labels)],
        text=values, textposition="outside",
        textfont=dict(color="#f1f5f9"),
        hovertemplate="%{y}: %{x} events<extra></extra>"
    ))
    fig.update_xaxis(title="Count")
    _apply_layout(fig, "MD Fault Type Breakdown", height=280)
    return fig


def qoq_comparison_bar(metrics_by_quarter: dict, top_n=15):
    # metrics_by_quarter: {quarter_label: metrics_df}
    all_suppliers = None
    for q, df in metrics_by_quarter.items():
        top = df.nlargest(top_n, "total_lines_ordered")["supplier_name"]
        all_suppliers = top if all_suppliers is None else all_suppliers[all_suppliers.isin(top)]
    # union of top suppliers
    union_suppliers = set()
    for q, df in metrics_by_quarter.items():
        union_suppliers.update(df.nlargest(top_n, "total_lines_ordered")["supplier_name"].tolist())
    union_suppliers = list(union_suppliers)[:top_n]

    fig = go.Figure()
    palette = ["#0d9488", "#16a34a", "#d97706", "#ea580c", "#dc2626"]
    for i, (q_label, df) in enumerate(metrics_by_quarter.items()):
        sub = df[df["supplier_name"].isin(union_suppliers)].set_index("supplier_name")
        suppliers = union_suppliers
        y_vals = [sub.loc[s, "friction_index"] if s in sub.index else 0 for s in suppliers]
        fig.add_trace(go.Bar(
            name=q_label, x=suppliers, y=y_vals,
            marker_color=palette[i % len(palette)],
            hovertemplate="<b>%{x}</b><br>" + q_label + ": %{y:.2f}<extra></extra>"
        ))
    fig.update_layout(barmode="group")
    fig.update_xaxis(tickangle=-35)
    fig.update_yaxis(title="Friction Index")
    _apply_layout(fig, "Quarter-over-Quarter Friction Index Comparison (Top Suppliers by Volume)", height=430)
    return fig
