import pandas as pd
import numpy as np

GRADE_ORDER = ["OUTSTANDING", "EXCELLENT", "ACCEPTABLE", "WATCH", "AT RISK", "CRITICAL"]

def friction_grade(fi):
    if fi == 0:
        return "OUTSTANDING"
    elif fi <= 2.0:
        return "EXCELLENT"
    elif fi <= 8.0:
        return "ACCEPTABLE"
    elif fi <= 20.0:
        return "WATCH"
    elif fi <= 50.0:
        return "AT RISK"
    else:
        return "CRITICAL"


def compute_friction_metrics(df, start_date=None, end_date=None, categories=None,
                              criticalities=None, projects=None):
    d = df.copy()
    if start_date:
        d = d[d["order_date"] >= pd.Timestamp(start_date)]
    if end_date:
        d = d[d["order_date"] <= pd.Timestamp(end_date)]
    if categories:
        d = d[d["component_category"].isin(categories)]
    if criticalities:
        d = d[d["component_criticality"].isin(criticalities)]
    if projects:
        d = d[d["project_number"].isin(projects)]

    if d.empty:
        return pd.DataFrame()

    max_lines = d.groupby("supplier_name").size().max()

    records = []
    for supplier, grp in d.groupby("supplier_name"):
        n = len(grp)
        commit_minus_request = (pd.to_datetime(grp["commit_date"]) - pd.to_datetime(grp["request_date"])).dt.days
        avg_commit_gap = commit_minus_request.mean()
        planning_score = max(0.0, 1.0 - avg_commit_gap * 0.02)

        volume_weight = (n / max_lines) * 0.5 + 0.5

        late_arr  = grp["is_late_arrived"].sum()
        open_late = grp["is_open_late"].sum()
        pct_late_arrived = (late_arr / n) * 100
        pct_open_late    = (open_late / n) * 100

        late_days = grp.loc[grp["is_late_arrived"], "days_late"].dropna()
        prop_severe    = (late_days > 20).sum() / n if n > 0 else 0
        severity_factor = 1 + prop_severe * 2

        ps = planning_score if planning_score > 0 else 0.01
        friction_index = ((pct_late_arrived + pct_open_late * 8) / ps) * volume_weight * severity_factor
        friction_index = round(friction_index, 4)

        avg_days_late = late_days.mean() if len(late_days) > 0 else 0.0
        total_spend   = grp["line_spend_usd"].sum()
        at_risk_spend = grp.loc[grp["is_late_arrived"] | grp["is_open_late"], "line_spend_usd"].sum()

        records.append({
            "supplier_name":        supplier,
            "total_lines_ordered":  n,
            "total_spend_usd":      round(total_spend, 2),
            "at_risk_spend_usd":    round(at_risk_spend, 2),
            "count_late_arrived":   int(late_arr),
            "count_open_late":      int(open_late),
            "pct_late_arrived":     round(pct_late_arrived, 2),
            "pct_open_late":        round(pct_open_late, 2),
            "avg_days_late":        round(float(avg_days_late), 1),
            "planning_score":       round(planning_score, 4),
            "volume_weight":        round(volume_weight, 4),
            "severity_factor":      round(severity_factor, 4),
            "friction_index":       friction_index,
            "grade":                friction_grade(friction_index),
        })

    result = pd.DataFrame(records)
    result["grade_order"] = result["grade"].map({g: i for i, g in enumerate(GRADE_ORDER)})
    return result.sort_values("friction_index", ascending=False).reset_index(drop=True)


def compute_md_metrics(df, start_date=None, end_date=None, categories=None,
                        criticalities=None, projects=None):
    d = df.copy()
    if start_date:
        d = d[d["order_date"] >= pd.Timestamp(start_date)]
    if end_date:
        d = d[d["order_date"] <= pd.Timestamp(end_date)]
    if categories:
        d = d[d["component_category"].isin(categories)]
    if criticalities:
        d = d[d["component_criticality"].isin(criticalities)]
    if projects:
        d = d[d["project_number"].isin(projects)]

    md = d[d["has_md_event"]].copy()
    records = []
    for supplier, grp in md.groupby("supplier_name"):
        total_mda  = len(grp)
        sf_count   = grp["is_supplier_fault"].sum()
        pct_sf     = round((sf_count / total_mda) * 100, 1) if total_mda > 0 else 0
        rework_cost = grp["cost_of_rework_usd"].sum()
        days_lost  = grp["days_lost_to_md"].sum()
        fault_breakdown = grp["md_fault_type"].value_counts().to_dict()
        md_flag = "⚠️ FLAG" if pct_sf > 50 else "✅ PASS"
        records.append({
            "supplier_name":          supplier,
            "open_mdas":              total_mda,
            "supplier_fault_count":   int(sf_count),
            "pct_supplier_fault":     pct_sf,
            "total_rework_cost_usd":  round(float(rework_cost), 2),
            "total_days_lost":        int(days_lost),
            "md_flag":                md_flag,
            "fault_breakdown":        fault_breakdown,
        })
    return pd.DataFrame(records).sort_values("open_mdas", ascending=False).reset_index(drop=True)


def compute_monthly_friction(df, supplier_name):
    grp = df[df["supplier_name"] == supplier_name].copy()
    grp["month"] = pd.to_datetime(grp["order_date"]).dt.to_period("M")
    max_lines = len(grp)
    records = []
    for month, mgrp in grp.groupby("month"):
        n = len(mgrp)
        commit_gap = (pd.to_datetime(mgrp["commit_date"]) - pd.to_datetime(mgrp["request_date"])).dt.days.mean()
        ps  = max(0.01, 1.0 - commit_gap * 0.02)
        vw  = (n / max(max_lines, 1)) * 0.5 + 0.5
        pct_la = (mgrp["is_late_arrived"].sum() / n) * 100
        pct_ol = (mgrp["is_open_late"].sum() / n)   * 100
        late_days  = mgrp.loc[mgrp["is_late_arrived"], "days_late"].dropna()
        prop_sev   = (late_days > 20).sum() / n if n > 0 else 0
        sf = 1 + prop_sev * 2
        fi = round(((pct_la + pct_ol * 8) / ps) * vw * sf, 4)
        records.append({"month": str(month), "friction_index": fi, "lines": n})
    return pd.DataFrame(records)
