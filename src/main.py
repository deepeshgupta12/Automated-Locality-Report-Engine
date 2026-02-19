from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from src.data_io.json_loader import load_json
from src.transform.extract_sources import extract_sources
from src.validate.quality import validate_inputs


def _write_json(path: Path, obj: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def build_report_payload(sources: Dict[str, Any]) -> Dict[str, Any]:
    """
    Step-1 payload: merged canonical sources + page-wise placeholders wired to your 12-page architecture.
    No charts rendered here. No LLM calls here.
    """
    j1 = sources["json1_locality"]
    j2 = sources["json2_rates"]

    loc_name = (j1.get("localityOverviewData") or {}).get("name")
    city = (j1.get("localityOverviewData") or {}).get("cityName")
    micro = (j1.get("localityOverviewData") or {}).get("dotcomLocationName")

    # NOTE: polygon image URL is external input (static)
    polygon_url = "https://static.squareyards.com/localitymap-thumnail/andheri-east-mumbai-v3.png"

    meta = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "locality": loc_name,
        "city": city,
        "micromarket": micro,
        "version": "step1_merge_validate",
    }

    assets = {
        "polygon_thumbnail_url": polygon_url,
    }

    payload: Dict[str, Any] = {
        "meta": meta,
        "assets": assets,
        "sources": {
            "json1_locality": {
                "localityOverviewData": j1.get("localityOverviewData"),
                "ratingReviewData": j1.get("ratingReviewData"),
                "demandSupply": j1.get("demandSupply"),
                "govtRegistration": j1.get("govtRegistration"),
                "marketSupply": j1.get("marketSupply"),
                "rentalStats": j1.get("rentalStats"),
                "recentTransactions": j1.get("recentTransactions"),
                "indices": j1.get("indices"),
                "landmarks": j1.get("landmarks"),
                "ratingReview": j1.get("ratingReview"),
            },
            "json2_rates": {
                "details": j2.get("details"),
                "marketOverview": j2.get("marketOverview"),
                "priceTrend": j2.get("priceTrend"),
                "locationRates": j2.get("locationRates"),
                "propertyTypes": j2.get("propertyTypes"),
                "propertyStatus": j2.get("propertyStatus"),
                "topProjects": j2.get("topProjects"),
                "govtRegistration": j2.get("govtRegistration"),
                "topDevelopers": j2.get("topDevelopers"),
            },
        },

        "page1_cover": {
            "data": {
                "title": f"{loc_name} Locality Report" if loc_name else "Locality Report",
                "city": city,
                "micromarket": micro,
                "polygon_thumbnail_url": polygon_url,
            },
            "narrative_inputs": {
                "locality": loc_name,
                "city": city,
                "micromarket": micro,
            },
        },

        "page2_exec_snapshot": {
            "data": {
                "marketOverview": j2.get("marketOverview"),
                "ratingReviewData": j1.get("ratingReviewData"),
                "rentalStats": j1.get("rentalStats"),
                "demandSupply_sale": (j1.get("demandSupply") or {}).get("sale"),
                "demandSupply_rent": (j1.get("demandSupply") or {}).get("rent"),
                "priceTrend": j2.get("priceTrend"),
                "govtRegistration_json1": j1.get("govtRegistration"),
                "govtRegistration_json2": j2.get("govtRegistration"),
            },
            "computed": {},
            "narrative_inputs": {},
        },

        "page3_liveability": {
            "data": {
                "localityOverviewData": j1.get("localityOverviewData"),
                "indices": j1.get("indices"),
                "landmarks": j1.get("landmarks"),
            },
            "narrative_inputs": {},
        },

        "page4_market_snapshot": {
            "data": {
                "marketSupply": j1.get("marketSupply"),
                "rentalStats": j1.get("rentalStats"),
                "marketOverview": j2.get("marketOverview"),
            },
            "narrative_inputs": {},
        },

        "page5_price_trend": {"data": {"priceTrend": j2.get("priceTrend")}, "narrative_inputs": {}},
        "page6_nearby_comparison": {"data": {"locationRates": j2.get("locationRates")}, "narrative_inputs": {}},
        "page7_demand_supply_sale": {
            "data": {"sale": (j1.get("demandSupply") or {}).get("sale")},
            "computed": {},
            "narrative_inputs": {},
        },
        "page8_demand_supply_rent": {
            "data": {"rent": (j1.get("demandSupply") or {}).get("rent")},
            "computed": {},
            "narrative_inputs": {},
        },
        "page9_propertytype_status": {
            "data": {"propertyTypes": j2.get("propertyTypes"), "propertyStatus": j2.get("propertyStatus")},
            "narrative_inputs": {},
        },
        "page10_top_projects": {"data": {"topProjects": j2.get("topProjects")}, "narrative_inputs": {}},
        "page11_registrations_developers": {
            "data": {
                "govtRegistration_json1": j1.get("govtRegistration"),
                "govtRegistration_json2": j2.get("govtRegistration"),
                "topDevelopers": j2.get("topDevelopers"),
                "recentTransactions": j1.get("recentTransactions"),
            },
            "narrative_inputs": {},
        },
        "page12_reviews_conclusion": {
            "data": {
                "ratingReviewData": j1.get("ratingReviewData"),
                "ratingReview": j1.get("ratingReview"),
                "insights_inputs_json2": {
                    "marketOverview": j2.get("marketOverview"),
                    "priceTrend": j2.get("priceTrend"),
                    "locationRates": j2.get("locationRates"),
                    "propertyTypes": j2.get("propertyTypes"),
                    "propertyStatus": j2.get("propertyStatus"),
                    "topProjects": j2.get("topProjects"),
                    "govtRegistration": j2.get("govtRegistration"),
                    "topDevelopers": j2.get("topDevelopers"),
                },
            },
            "narrative_inputs": {},
        },
    }

    return payload


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json1", required=True, help="Path to Locality.json")
    ap.add_argument("--json2", required=True, help="Path to Property Rates.json")
    ap.add_argument("--out", default="out", help="Output folder")
    args = ap.parse_args()

    json1 = load_json(args.json1)
    json2 = load_json(args.json2)

    validation = validate_inputs(json1, json2)
    sources = extract_sources(json1, json2)
    report_payload = build_report_payload(sources)

    out_dir = Path(args.out)
    _write_json(out_dir / "report_payload.json", report_payload)

    quality_report = {
        "inputs": {"json1_path": args.json1, "json2_path": args.json2},
        "validation": validation,
        "notes": [
            "Step 1 merges + validates only. No charts or LLM narrative is generated here.",
            "Warnings represent optional blocks missing in the provided JSONs (no assumptions made).",
        ],
    }
    _write_json(out_dir / "quality_report.json", quality_report)

    print("Done.")
    print(f"Report payload: {out_dir / 'report_payload.json'}")
    print(f"Quality report: {out_dir / 'quality_report.json'}")

    if validation["errors"]:
        print("Validation errors found. Open out/quality_report.json for details.")
    else:
        print("No validation errors. (Warnings may still exist.)")


if __name__ == "__main__":
    main()