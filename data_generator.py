import numpy as np
import pandas as pd
from datetime import date, timedelta

def generate_dataset(seed=42, n_rows=500):
    rng = np.random.default_rng(seed)
    today = date(2026, 4, 29)

    SUPPLIER_PROFILES = {
        "EXCELLENT": [
            "Apex Precision Components", "Meridian Fastener Corp", "Summit Hydraulics LLC",
            "Pacific Alloy Works", "Vega Electronics Ltd", "Ironclad Assemblies",
            "Cascade Tooling Solutions", "Keystone Bearing Systems", "Stratos Machined Parts",
            "Alpine Fabrications Inc", "Polaris Metals Group", "Helix Precision Mfg",
            "Crestline Tooling Co", "NorthStar Electro-Mech", "Zenith Alloy Solutions"
        ],
        "ACCEPTABLE": [
            "Delta Machining Group", "Tri-State Fabricators Inc", "Cornerstone Electro-Mech",
            "Harbor Castings LLC", "Redwood Stampings Inc", "Mesa Components Corp",
            "Lakeview Thermal Systems", "Ridgeline Hydraulics", "Silverado Machining",
            "BlueSky Structural Inc", "Coastal Precision Parts", "Granite Valley Mfg",
            "Ironwood Tooling Group", "Prairie Industrial Supply", "Western Alloy Fab",
            "Canyon Fabricators LLC", "Eagle Ridge Components", "Horizon Mech Solutions",
            "Lakewood Electro Systems", "Timberline Fasteners"
        ],
        "WATCH": [
            "Foxridge Assemblies", "Dusk Manufacturing Co", "Bayside Precision LLC",
            "Trident Industrial Parts", "Crestfall Components", "Lowland Metal Works",
            "Greystone Fabrications"
        ],
        "CRITICAL": [
            "Riverton Manufacturing", "Hollowpoint Alloys Inc", "Badlands Components LLC"
        ]
    }

    all_suppliers = []
    profile_map = {}
    for profile, names in SUPPLIER_PROFILES.items():
        for name in names:
            all_suppliers.append(name)
            profile_map[name] = profile

    volume_weights = {}
    for name in all_suppliers:
        profile = profile_map[name]
        if profile == "EXCELLENT":
            volume_weights[name] = rng.integers(8, 20)
        elif profile == "ACCEPTABLE":
            volume_weights[name] = rng.integers(5, 18)
        elif profile == "WATCH":
            volume_weights[name] = rng.integers(10, 35)
        else:
            volume_weights[name] = rng.integers(15, 50)

    high_vol = rng.choice(all_suppliers, size=6, replace=False)
    for s in high_vol:
        volume_weights[s] += rng.integers(30, 80)

    supplier_probs = np.array([volume_weights[s] for s in all_suppliers], dtype=float)
    supplier_probs /= supplier_probs.sum()

    CATEGORIES = ["Mechanical", "Electrical", "Optical", "Hydraulic", "Structural", "Thermal Management"]
    COST_RANGES = {
        "Mechanical": (50, 5000), "Electrical": (100, 15000), "Optical": (500, 50000),
        "Hydraulic": (200, 8000), "Structural": (30, 2000), "Thermal Management": (150, 6000)
    }
    CRITICALITIES = ["Standard", "High", "Critical"]
    CRIT_WEIGHTS = [0.5, 0.3, 0.2]
    MD_FAULT_TYPES = ["Poor Workmanship", "Wrong Part Delivered", "Damaged in Transit",
                      "Supplier BOM Error", "Dimension Non-Conformance", "Surface Finish Defect"]
    PROJECT_NUMBERS = [f"PRJ-{rng.integers(1000, 9999)}" for _ in range(12)]

    start_date = date(2024, 1, 1)
    end_date = date(2026, 3, 31)
    date_range = (end_date - start_date).days

    # Alpine-specific: track order count to inject realistic slips on ~20% of lines
    alpine_order_count = 0

    rows = []
    for i in range(n_rows):
        supplier = rng.choice(all_suppliers, p=supplier_probs)
        profile = profile_map[supplier]
        order_date = start_date + timedelta(days=int(rng.integers(0, date_range)))
        lead_days = int(rng.integers(14, 91))
        request_date = order_date + timedelta(days=lead_days)

        if profile == "EXCELLENT":
            commit_offset = int(rng.integers(-5, 6))
        elif profile == "ACCEPTABLE":
            commit_offset = int(rng.integers(0, 16))
        elif profile == "WATCH":
            commit_offset = int(rng.integers(5, 31))
        else:
            commit_offset = int(rng.integers(10, 51))

        commit_date = request_date + timedelta(days=commit_offset)

        category = rng.choice(CATEGORIES)
        criticality = rng.choice(CRITICALITIES, p=CRIT_WEIGHTS)
        lo, hi = COST_RANGES[category]
        unit_cost = round(float(rng.uniform(lo, hi)), 2)
        qty = int(rng.exponential(20)) + 1
        qty = min(qty, 200)

        open_late = False
        received_date = None

        if supplier == "Alpine Fabrications Inc":
            # ~20% of Alpine lines arrive 5-10 days past commit — enough to cross the >4 threshold
            # Remaining 80% arrive on time or 1-2 days early/late (below threshold)
            alpine_order_count += 1
            if rng.random() < 0.20:
                recv_offset = int(rng.integers(5, 11))  # 5 to 10 days late — triggers >4
            else:
                recv_offset = int(rng.integers(-2, 4))  # -2 to +3 days — stays below threshold
            received_date = commit_date + timedelta(days=recv_offset)
            if received_date < order_date:
                received_date = order_date + timedelta(days=1)
        elif profile == "EXCELLENT":
            recv_offset = int(rng.integers(-2, 3))
            received_date = commit_date + timedelta(days=recv_offset)
            if received_date < order_date:
                received_date = order_date + timedelta(days=1)
        elif profile == "ACCEPTABLE":
            on_time = rng.random() < 0.75
            recv_offset = int(rng.integers(0, 9)) if not on_time else int(rng.integers(-1, 2))
            received_date = commit_date + timedelta(days=recv_offset)
        elif profile == "WATCH":
            if rng.random() < 0.03:
                open_late = True
                received_date = None
            else:
                on_time = rng.random() < 0.55
                recv_offset = int(rng.integers(0, 21)) if not on_time else int(rng.integers(-1, 3))
                received_date = commit_date + timedelta(days=recv_offset)
        else:  # CRITICAL
            if rng.random() < 0.08:
                open_late = True
                received_date = None
            else:
                on_time = rng.random() < 0.30
                recv_offset = int(rng.integers(5, 46)) if not on_time else int(rng.integers(0, 8))
                received_date = commit_date + timedelta(days=recv_offset)

        is_late_arrived = False
        days_late = None
        if received_date is not None:
            delta = (received_date - commit_date).days
            is_late_arrived = delta > 4   # framework threshold — do not change
            days_late = max(0, delta)

        is_open_late = open_late and (today > commit_date + timedelta(days=4))

        md_probs = {"EXCELLENT": 0.03, "ACCEPTABLE": 0.10, "WATCH": 0.28, "CRITICAL": 0.42}
        has_md = rng.random() < md_probs[profile]
        md_fault_type = None
        is_supplier_fault = None
        cost_of_rework = None
        days_lost = None
        if has_md:
            md_fault_type = rng.choice(MD_FAULT_TYPES)
            is_supplier_fault = rng.random() < 0.70
            if is_supplier_fault:
                cost_of_rework = round(float(rng.uniform(200, 12000)), 2)
            days_lost = int(rng.integers(1, 26))

        quarter_map = {1: "Q1", 2: "Q1", 3: "Q1", 4: "Q2", 5: "Q2", 6: "Q2",
                       7: "Q3", 8: "Q3", 9: "Q3", 10: "Q4", 11: "Q4", 12: "Q4"}
        quarter = f"{quarter_map[order_date.month]}-{order_date.year}"

        rows.append({
            "order_id": f"PO-{order_date.year}-{str(i+1).zfill(5)}",
            "order_date": order_date,
            "supplier_name": supplier,
            "component_category": category,
            "component_criticality": criticality,
            "qty_ordered": qty,
            "unit_cost_usd": unit_cost,
            "request_date": request_date,
            "commit_date": commit_date,
            "received_date": received_date,
            "is_late_arrived": is_late_arrived,
            "is_open_late": is_open_late,
            "days_late": days_late,
            "has_md_event": has_md,
            "md_fault_type": md_fault_type,
            "is_supplier_fault": is_supplier_fault,
            "cost_of_rework_usd": cost_of_rework,
            "days_lost_to_md": days_lost,
            "project_number": rng.choice(PROJECT_NUMBERS),
            "quarter": quarter,
        })

    df = pd.DataFrame(rows)
    df["line_spend_usd"] = df["qty_ordered"] * df["unit_cost_usd"]
    return df


if __name__ == "__main__":
    import os
    df = generate_dataset()
    out_path = os.path.join(os.path.dirname(__file__), "supplier_order_lines.csv")
    df.to_csv(out_path, index=False)
    print(f"Generated {len(df)} rows -> {out_path}")
    alpine = df[df['supplier_name'] == 'Alpine Fabrications Inc']
    print(f"Alpine: {len(alpine)} lines, {alpine['is_late_arrived'].sum()} late (>{len(alpine)*0.15:.0f} expected)")
