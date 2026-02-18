from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from src.validate.schema import compute_gap_items, get_at_path, safe_number


Json = Dict[str, Any]


def _pick(root: Json, path: str) -> Any:
    found, value = get_at_path(root, path)
    return value if found else None


def _sum_listings(items: Optional[List[Dict[str, Any]]]) -> Optional[int]:
    if not items:
        return None
    total = 0
    for it in items:
        n = it.get("listing")
        nn = safe_number(n)
        if nn is None:
            continue
        total += int(round(nn))
    return total


def _top_gap(items_with_gap: List[Dict[str, Any]], *, positive: bool, k: int = 2) -> List[Dict[str, Any]]:
    filtered = [x for x in items_with_gap if isinstance(x.get("gap"), (int, float))]
    filtered.sort(key=lambda x: x["gap"], reverse=positive)
    return filtered[:k]


def build_report_payload(locality_json: Json, rates_json: Json, *, polygon_image_url: str) -> Dict[str, Any]:
    # JSON-1 extraction
    loc_name = _pick(locality_json, "data.localityOverviewData.name")
    city_name = _pick(locality_json, "data.localityOverviewData.cityName")
    micro_name = _pick(locality_json, "data.localityOverviewData.dotcomLocationName")

    rating_avg = _pick(locality_json, "ratingReviewData.AvgRating")
    rating_count = _pick(locality_json, "ratingReviewData.RatingCount")
    review_count = _pick(locality_json, "ratingReviewData.ReviewCount")

    # Demand/Supply (Sale)
    sale_unit = _pick(locality_json, "demandSupply.sale.unitType") or []
    sale_prop = _pick(locality_json, "demandSupply.sale.propertyType") or []
    sale_price = _pick(locality_json, "demandSupply.sale.totalPrice_range") or []

    sale_unit_gap = compute_gap_items(sale_unit) if isinstance(sale_unit, list) else []
    sale_prop_gap = compute_gap_items(sale_prop) if isinstance(sale_prop, list) else []
    sale_price_gap = compute_gap_items(sale_price) if isinstance(sale_price, list) else []

    # Demand/Supply (Rent)
    rent_unit = _pick(locality_json, "demandSupply.rent.unitType") or []
    rent_prop = _pick(locality_json, "demandSupply.rent.propertyType") or []
    rent_price = _pick(locality_json, "demandSupply.rent.totalPrice_range") or []

    rent_unit_gap = compute_gap_items(rent_unit) if isinstance(rent_unit, list) else []
    rent_prop_gap = compute_gap_items(rent_prop) if isinstance(rent_prop, list) else []
    rent_price_gap = compute_gap_items(rent_price) if isinstance(rent_price, list) else []

    # Govt Registration (JSON-1)
    reg1 = _pick(locality_json, "govtRegistration")
    market_supply = _pick(locality_json, "marketSupply")
    rental_stats = _pick(locality_json, "rentalStats")
    recent_tx = _pick(locality_json, "recentTransactions") or []
    indices = _pick(locality_json, "indices")

    # JSON-2 extraction
    market_overview = _pick(rates_json, "details.marketOverview")
    price_trend = _pick(rates_json, "details.priceTrend") or []
    location_rates = _pick(rates_json, "details.locationRates") or []
    property_types = _pick(rates_json, "details.propertyTypes") or []
    property_status = _pick(rates_json, "details.propertyStatus") or []
    top_projects = _pick(rates_json, "details.topProjects") or {}
    top_developers = _pick(rates_json, "details.topDevelopers") or {}
    reg2 = _pick(rates_json, "details.govtRegistration")

    # Derived snapshot metrics
    sale_total_listings = _sum_listings(sale_unit)  # sum of listings by BHK
    rent_total_listings = _sum_listings(rent_unit)

    payload: Dict[str, Any] = {
        "meta": {
            "locality": loc_name,
            "city": city_name,
            "micromarket": micro_name,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "schema_version": "v1_step1",
        },
        "assets": {
            "polygon_image_url": polygon_image_url,
        },
        "sources": {
            "json1_locality": {
                "localityOverviewData": _pick(locality_json, "data.localityOverviewData"),
                "ratingReviewData": _pick(locality_json, "ratingReviewData"),
                "demandSupply": _pick(locality_json, "demandSupply"),
                "govtRegistration": reg1,
                "marketSupply": market_supply,
                "rentalStats": rental_stats,
                "recentTransactions": recent_tx,
                "indices": indices,
            },
            "json2_rates": {
                "marketOverview": market_overview,
                "priceTrend": price_trend,
                "locationRates": location_rates,
                "propertyTypes": property_types,
                "propertyStatus": property_status,
                "topProjects": top_projects,
                "govtRegistration": reg2,
                "topDevelopers": top_developers,
            },
        },

        # Page-wise blocks (data + computed + narrative_inputs)
        "page1_cover": {
            "data": {
                "locality": loc_name,
                "city": city_name,
                "micromarket": micro_name,
                "polygon_image_url": polygon_image_url,
            },
            "computed": {},
            "narrative_inputs": {
                "title_line": f"{loc_name} Locality Report" if loc_name else "Locality Report",
                "subtitle_line": f"{city_name} | {micro_name}" if city_name and micro_name else None,
            },
        },

        "page2_exec_snapshot": {
            "data": {
                "marketOverview": market_overview,
                "ratingReviewData": {
                    "AvgRating": rating_avg,
                    "RatingCount": rating_count,
                    "ReviewCount": review_count,
                },
                "sale_total_listings": sale_total_listings,
                "rent_total_listings": rent_total_listings,
                "rentalStats": rental_stats,
            },
            "computed": {
                "sale_top_under_supplied_bhk": _top_gap(sale_unit_gap, positive=True, k=2),
                "sale_top_over_supplied_bhk": _top_gap(sale_unit_gap, positive=False, k=2),
                "rent_top_under_supplied_bhk": _top_gap(rent_unit_gap, positive=True, k=2),
                "rent_top_over_supplied_bhk": _top_gap(rent_unit_gap, positive=False, k=2),
            },
            "narrative_inputs": {
                "price_trend_points": price_trend[-4:] if isinstance(price_trend, list) else [],
                "marketOverview": market_overview,
                "rating_summary": {"avg": rating_avg, "count": rating_count},
            },
        },

        "page3_liveability": {
            "data": {
                "indices": indices,
            },
            "computed": {},
            "narrative_inputs": {
                "indices_html": {
                    "connectivity_text": _pick(locality_json, "indices.connectivity_text"),
                    "lifestyle_text": _pick(locality_json, "indices.lifestyle_text"),
                    "educationhealth_text": _pick(locality_json, "indices.educationhealth_text"),
                    "livability_text": _pick(locality_json, "indices.livability_text"),
                }
            },
        },

        "page4_market_snapshot": {
            "data": {
                "marketOverview": market_overview,
                "marketSupply": market_supply,
                "rentalStats": rental_stats,
            },
            "computed": {},
            "narrative_inputs": {
                "supply_histogram": _pick(locality_json, "marketSupply.graphData"),
                "rental_bhk_stats": _pick(locality_json, "rentalStats.rentalBHKStats"),
            },
        },

        "page5_price_trend": {
            "data": {
                "priceTrend": price_trend,
            },
            "computed": {
                "trend_points_count": len(price_trend) if isinstance(price_trend, list) else 0,
            },
            "narrative_inputs": {
                "priceTrend": price_trend,
            },
        },

        "page6_nearby_comparison": {
            "data": {
                "locationRates": location_rates,
            },
            "computed": {},
            "narrative_inputs": {
                "locationRates": location_rates,
            },
        },

        "page7_demand_supply_sale": {
            "data": {
                "unitType": sale_unit,
                "propertyType": sale_prop,
                "totalPrice_range": sale_price,
            },
            "computed": {
                "unitType_with_gap": sale_unit_gap,
                "propertyType_with_gap": sale_prop_gap,
                "totalPrice_range_with_gap": sale_price_gap,
                "top_under_supplied": {
                    "unitType": _top_gap(sale_unit_gap, positive=True, k=3),
                    "propertyType": _top_gap(sale_prop_gap, positive=True, k=3),
                    "totalPrice_range": _top_gap(sale_price_gap, positive=True, k=3),
                },
                "top_over_supplied": {
                    "unitType": _top_gap(sale_unit_gap, positive=False, k=3),
                    "propertyType": _top_gap(sale_prop_gap, positive=False, k=3),
                    "totalPrice_range": _top_gap(sale_price_gap, positive=False, k=3),
                },
            },
            "narrative_inputs": {
                "unitType_with_gap": sale_unit_gap,
                "propertyType_with_gap": sale_prop_gap,
                "totalPrice_range_with_gap": sale_price_gap,
            },
        },

        "page8_demand_supply_rent": {
            "data": {
                "unitType": rent_unit,
                "propertyType": rent_prop,
                "totalPrice_range": rent_price,
            },
            "computed": {
                "unitType_with_gap": rent_unit_gap,
                "propertyType_with_gap": rent_prop_gap,
                "totalPrice_range_with_gap": rent_price_gap,
                "top_under_supplied": {
                    "unitType": _top_gap(rent_unit_gap, positive=True, k=3),
                    "propertyType": _top_gap(rent_prop_gap, positive=True, k=3),
                    "totalPrice_range": _top_gap(rent_price_gap, positive=True, k=3),
                },
                "top_over_supplied": {
                    "unitType": _top_gap(rent_unit_gap, positive=False, k=3),
                    "propertyType": _top_gap(rent_prop_gap, positive=False, k=3),
                    "totalPrice_range": _top_gap(rent_price_gap, positive=False, k=3),
                },
            },
            "narrative_inputs": {
                "unitType_with_gap": rent_unit_gap,
                "propertyType_with_gap": rent_prop_gap,
                "totalPrice_range_with_gap": rent_price_gap,
            },
        },

        "page9_propertytype_status": {
            "data": {
                "propertyTypes": property_types,
                "propertyStatus": property_status,
            },
            "computed": {},
            "narrative_inputs": {
                "propertyTypes": property_types,
                "propertyStatus": property_status,
            },
        },

        "page10_top_projects": {
            "data": {
                "topProjects": top_projects,
            },
            "computed": {},
            "narrative_inputs": {
                "byListingRates": (top_projects or {}).get("byListingRates"),
                "byTransactions": (top_projects or {}).get("byTransactions"),
                "byValue": (top_projects or {}).get("byValue"),
            },
        },

        "page11_registrations_developers": {
            "data": {
                "govtRegistration_primary": reg2,
                "govtRegistration_secondary": reg1,
                "topDevelopers": top_developers,
                "recentTransactions": recent_tx,
            },
            "computed": {
                "has_mismatch_govt_registration": bool(reg2 and reg1 and reg2 != reg1),
            },
            "narrative_inputs": {
                "govtRegistration": reg2 or reg1,
                "topDevelopers_byTransactions": (top_developers or {}).get("byTransactions"),
                "topDevelopers_byValue": (top_developers or {}).get("byValue"),
            },
        },

        "page12_reviews_conclusion": {
            "data": {
                "ratingReviewData": {
                    "AvgRating": rating_avg,
                    "RatingCount": rating_count,
                    "ReviewCount": review_count,
                },
                # These may or may not exist; we won't assume. Validator will report.
                "ratingStarCount": _pick(locality_json, "ratingReview.ratingStarCount"),
                "topReviews": _pick(locality_json, "ratingReview.topReviews"),
                "localityAttributes": _pick(locality_json, "localityAttributes"),
            },
            "computed": {},
            "narrative_inputs": {
                "marketOverview": market_overview,
                "priceTrend": price_trend,
                "locationRates": location_rates,
                "propertyTypes": property_types,
                "propertyStatus": property_status,
                "topProjects": top_projects,
                "govtRegistration": reg2 or reg1,
                "topDevelopers": top_developers,
                "rating_summary": {"avg": rating_avg, "count": rating_count, "reviews": review_count},
            },
        },
    }

    return payload


def required_key_specs() -> Dict[str, List[Tuple[str, Any]]]:
    """
    Required keys: only what you explicitly said we will use.
    If missing, we'll flag and later render placeholders (we won't invent).
    """
    json1_required: List[Tuple[str, Any]] = [
        ("data.localityOverviewData.name", str),
        ("data.localityOverviewData.dotcomLocationName", str),
        ("data.localityOverviewData.cityName", str),

        ("ratingReviewData.AvgRating", (int, float)),
        ("ratingReviewData.RatingCount", (int, float)),
        ("ratingReviewData.ReviewCount", (int, float)),

        ("demandSupply.sale.unitType", list),
        ("demandSupply.sale.propertyType", list),
        ("demandSupply.sale.totalPrice_range", list),

        ("demandSupply.rent.unitType", list),
        ("demandSupply.rent.propertyType", list),
        ("demandSupply.rent.totalPrice_range", list),

        ("govtRegistration", dict),
        ("marketSupply", dict),
        ("rentalStats", dict),
        ("recentTransactions", list),
        ("indices", dict),
    ]

    json2_required: List[Tuple[str, Any]] = [
        ("details.marketOverview", dict),
        ("details.priceTrend", list),
        ("details.locationRates", list),
        ("details.propertyTypes", list),
        ("details.propertyStatus", list),
        ("details.topProjects", dict),
        ("details.govtRegistration", dict),
        ("details.topDevelopers", dict),
    ]

    return {"json1_required": json1_required, "json2_required": json2_required}