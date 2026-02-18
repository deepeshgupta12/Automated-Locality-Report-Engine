from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict

from src.render.charts import (
    chart_dual_gap_bars,
    chart_histogram_buckets,
    chart_nearby_rates,
    chart_price_trend,
    chart_rent_by_bhk,
    chart_simple_bar,
)
from src.render.pdf import render_pdf


def _read_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _write_json(path: Path, obj: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True, help="Path to report_payload_step2.json")
    ap.add_argument("--outdir", required=True, help="Output directory")
    args = ap.parse_args()

    inp_path = Path(args.inp).expanduser()
    outdir = Path(args.outdir).expanduser()
    outdir.mkdir(parents=True, exist_ok=True)

    payload = _read_json(inp_path)

    charts_dir = outdir / "charts"
    charts_dir.mkdir(parents=True, exist_ok=True)

    charts: Dict[str, str] = {}

    # Page 4 charts
    try:
        p4 = payload.get("page4_market_snapshot", {})
        ms = (p4.get("data", {}) or {}).get("marketSupply", {}) or {}
        gd = ms.get("graphData") or []
        if gd:
            out = charts_dir / "p4_supply_hist.png"
            chart_histogram_buckets(gd, out)
            charts["p4_supply_hist"] = str(out)

        rental = (p4.get("data", {}) or {}).get("rentalStats", {}) or {}
        rb = rental.get("rentalBHKStats") or []
        if rb:
            out = charts_dir / "p4_rent_bhk.png"
            chart_rent_by_bhk(rb, out)
            charts["p4_rent_bhk"] = str(out)
    except Exception:
        # Keep deterministic behavior: missing chart => no path, page still renders placeholders.
        pass

    # Page 5 trend chart
    try:
        p5 = payload.get("page5_price_trend", {})
        pts = (p5.get("computed", {}) or {}).get("points") or (p5.get("data", {}) or {}).get("priceTrend") or []
        if pts:
            out = charts_dir / "p5_price_trend.png"
            chart_price_trend(pts, out)
            charts["p5_price_trend"] = str(out)
    except Exception:
        pass

    # Page 6 nearby
    try:
        p6 = payload.get("page6_nearby_comparison", {})
        loc_rates = (p6.get("data", {}) or {}).get("locationRates") or []
        if loc_rates:
            out = charts_dir / "p6_nearby_bar.png"
            chart_nearby_rates(loc_rates, out, max_n=10)
            charts["p6_nearby_bar"] = str(out)
    except Exception:
        pass

    # Page 7/8 demand-supply charts
    def build_ds_arrays(d: Dict[str, Any], page_no: int) -> None:
        """
        d must be a dict containing:
          unitType[], propertyType[], totalPrice_range[]
        """
        unit = d.get("unitType") or []
        ptype = d.get("propertyType") or []
        band = d.get("totalPrice_range") or []

        if unit:
            out = charts_dir / f"p{page_no}_ds_unit.png"
            chart_dual_gap_bars(unit, out, title="Demand vs Supply - Unit Type")
            charts[f"p{page_no}_ds_unit"] = str(out)
        if ptype:
            out = charts_dir / f"p{page_no}_ds_ptype.png"
            chart_dual_gap_bars(ptype, out, title="Demand vs Supply - Property Type")
            charts[f"p{page_no}_ds_ptype"] = str(out)
        if band:
            out = charts_dir / f"p{page_no}_ds_band.png"
            chart_dual_gap_bars(band, out, title="Demand vs Supply - Price Band")
            charts[f"p{page_no}_ds_band"] = str(out)

    # FIX: Page 7 uses data.sale (not data.demandSupply)
    try:
        p7 = payload.get("page7_demand_supply_sale", {})
        d7 = (p7.get("data", {}) or {}).get("sale") or {}
        if d7:
            build_ds_arrays(d7, 7)
    except Exception:
        pass

    # FIX: Page 8 uses data.rent (not data.demandSupply)
    try:
        p8 = payload.get("page8_demand_supply_rent", {})
        d8 = (p8.get("data", {}) or {}).get("rent") or {}
        if d8:
            build_ds_arrays(d8, 8)
    except Exception:
        pass

    # Page 9 propertyType + status
    try:
        p9 = payload.get("page9_propertytype_status", {})
        d9 = p9.get("data", {}) or {}
        ptypes = d9.get("propertyTypes") or []
        status = d9.get("propertyStatus") or []

        if ptypes:
            labels = [x.get("propertyType", "") for x in ptypes]
            values = [float(x.get("avgPrice") or 0.0) for x in ptypes]
            out = charts_dir / "p9_property_types.png"
            chart_simple_bar(labels, values, out, "Rates by Property Type", "Property Type", "Rate (₹/sq ft)", rotate=True)
            charts["p9_property_types"] = str(out)

        if status:
            labels = [x.get("status", "") for x in status]
            values = [float(x.get("avgPrice") or 0.0) for x in status]
            out = charts_dir / "p9_property_status.png"
            chart_simple_bar(labels, values, out, "Rates by Project Status", "Status", "Rate (₹/sq ft)", rotate=True)
            charts["p9_property_status"] = str(out)
    except Exception:
        pass

    # Page 11 developers by transactions
    try:
        p11 = payload.get("page11_registrations_developers", {})
        td = ((p11.get("data", {}) or {}).get("topDevelopers", {}) or {}).get("byTransactions", {}) or {}
        devs = td.get("developers") or []
        if devs:
            labels = [x.get("developerName", "") for x in devs]
            values = [float(x.get("noOfTransactions") or 0.0) for x in devs]
            out = charts_dir / "p11_devs_txn.png"
            chart_simple_bar(labels, values, out, "Top Developers by Transactions", "Developer", "Transactions", rotate=True)
            charts["p11_devs_txn"] = str(out)
    except Exception:
        pass

    # Attach charts into payload
    payload["charts"] = charts

    # Write step3 payload
    step3_payload_path = outdir / "report_payload_step3.json"
    _write_json(step3_payload_path, payload)

    # Render PDF
    locality = (payload.get("meta", {}) or {}).get("locality", "Locality")
    out_pdf = outdir / f"{locality} Locality Report.pdf"
    render_pdf(payload, out_pdf)

    # Quality report (keep your existing policy; optional improvement later)
    q = {
        "input": str(inp_path),
        "output_payload": str(step3_payload_path),
        "output_pdf": str(out_pdf),
        "charts_generated": list(charts.keys()),
        "warnings": [],
    }

    expected_pages = [
        "page1_cover",
        "page2_exec_snapshot",
        "page3_liveability",
        "page4_market_snapshot",
        "page5_price_trend",
        "page6_nearby_comparison",
        "page7_demand_supply_sale",
        "page8_demand_supply_rent",
        "page9_propertytype_status",
        "page10_top_projects",
        "page11_registrations_developers",
        "page12_reviews_conclusion",
    ]
    missing_pages = [p for p in expected_pages if p not in payload]
    if missing_pages:
        q["warnings"].append({"type": "missing_pages", "pages": missing_pages})

    missing_charts = []
    for k, pth in charts.items():
        try:
            if not Path(pth).exists():
                missing_charts.append({"chart": k, "path": pth})
        except Exception:
            missing_charts.append({"chart": k, "path": pth})
    if missing_charts:
        q["warnings"].append({"type": "chart_files_missing", "items": missing_charts})

    q_path = outdir / "quality_report_step3.json"
    _write_json(q_path, q)

    print("Done.")
    print(f"Step3 payload: {step3_payload_path}")
    print(f"Step3 quality report: {q_path}")
    print(f"PDF: {out_pdf}")
    if q["warnings"]:
        print(f"Warnings: {len(q['warnings'])} (see quality_report_step3.json)")
    else:
        print("No warnings.")


if __name__ == "__main__":
    main()