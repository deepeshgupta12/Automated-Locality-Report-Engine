from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple


MONTHS = {
    "jan": 1, "january": 1,
    "feb": 2, "february": 2,
    "mar": 3, "march": 3,
    "apr": 4, "april": 4,
    "may": 5,
    "jun": 6, "june": 6,
    "jul": 7, "july": 7,
    "aug": 8, "august": 8,
    "sep": 9, "sept": 9, "september": 9,
    "oct": 10, "october": 10,
    "nov": 11, "november": 11,
    "dec": 12, "december": 12,
}


def _safe_float(v: Any) -> Optional[float]:
    try:
        if v is None:
            return None
        if isinstance(v, (int, float)):
            return float(v)
        s = str(v).strip()
        s = re.sub(r"[^\d.\-]", "", s)
        return float(s) if s else None
    except Exception:
        return None


def parse_inr_compact(s: Any) -> Optional[float]:
    """
    Parses strings like:
      "₹ 25.7 K" => 25700
      "₹ 1.2 L"  => 120000
      "₹ 5,083 Cr" => 5083 * 1e7 (rupees) [but we usually keep Cr separately]
    Returns rupees as float when possible.
    """
    if s is None:
        return None
    if isinstance(s, (int, float)):
        return float(s)

    text = str(s)
    text = text.replace(",", "").strip()

    # Capture number + suffix
    m = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*([KkLl]|Cr|cr)?", text)
    if not m:
        return _safe_float(text)

    val = float(m.group(1))
    suf = (m.group(2) or "").lower()

    if suf == "k":
        return val * 1_000
    if suf == "l":
        return val * 100_000
    if suf == "cr":
        return val * 10_000_000
    return val


def parse_date_yyyy_mm_dd(s: Any) -> Optional[datetime]:
    if not s:
        return None
    try:
        return datetime.strptime(str(s), "%Y-%m-%d")
    except Exception:
        return None


def parse_date_range_end_label(date_range: Optional[str]) -> Optional[str]:
    """
    "Mar 25 to Feb 26" => "Feb 2026"
    Returns label only, not a date object.
    """
    if not date_range:
        return None
    txt = date_range.strip()
    # split by "to"
    if "to" not in txt:
        return None
    right = txt.split("to")[-1].strip()
    # right expected: "Feb 26"
    parts = right.split()
    if len(parts) < 2:
        return None
    mon = parts[0].strip().lower()
    yy = parts[1].strip()
    if mon not in MONTHS:
        return None
    # interpret 2-digit year as 20xx
    if len(yy) == 2 and yy.isdigit():
        year = 2000 + int(yy)
    else:
        year = int(re.sub(r"[^\d]", "", yy)) if re.sub(r"[^\d]", "", yy) else None
    if not year:
        return None
    month_name = parts[0].strip().title()
    return f"{month_name} {year}"


def html_ul_to_bullets(html: Optional[str]) -> List[str]:
    if not html:
        return []
    t = str(html)
    # remove outer tags
    t = t.replace("\n", " ")
    # extract li contents
    lis = re.findall(r"<li>(.*?)</li>", t, flags=re.IGNORECASE)
    bullets: List[str] = []
    for li in lis:
        li_clean = re.sub(r"<.*?>", "", li).strip()
        if li_clean:
            bullets.append(li_clean)
    # fallback: strip all tags and split sentences
    if not bullets:
        clean = re.sub(r"<.*?>", "", t).strip()
        if clean:
            bullets = [clean]
    return bullets


def sum_listings(items: List[Dict[str, Any]]) -> int:
    total = 0
    for it in items or []:
        n = it.get("listing")
        if isinstance(n, (int, float)):
            total += int(n)
        else:
            f = _safe_float(n)
            total += int(f) if f is not None else 0
    return total


def compute_gap_table(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for it in items or []:
        demand = _safe_float(it.get("demandPercent"))
        supply = _safe_float(it.get("supplyPercent"))
        gap = None
        if demand is not None and supply is not None:
            gap = demand - supply
        out.append({
            "name": it.get("name"),
            "listing": it.get("listing"),
            "demandPercent": demand,
            "supplyPercent": supply,
            "gap": gap,
        })
    return out


def top_gaps(gap_table: List[Dict[str, Any]], k: int = 2) -> Dict[str, List[Dict[str, Any]]]:
    valid = [r for r in gap_table if isinstance(r.get("gap"), (int, float))]
    under = sorted([r for r in valid if r["gap"] > 0], key=lambda x: x["gap"], reverse=True)[:k]
    over = sorted([r for r in valid if r["gap"] < 0], key=lambda x: x["gap"])[:k]
    return {"under_supplied": under, "over_supplied": over}


def compute_price_trend_summary(price_trend: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not price_trend:
        return {"points": [], "total_change_pct_locality": None, "total_change_pct_micromarket": None}
    pts = []
    for p in price_trend:
        pts.append({
            "quarterName": p.get("quarterName"),
            "locationRate": _safe_float(p.get("locationRate")),
            "micromarketRate": _safe_float(p.get("micromarketRate")),
        })
    # total pct = (last-first)/first
    first_loc = pts[0].get("locationRate")
    last_loc = pts[-1].get("locationRate")
    first_mm = pts[0].get("micromarketRate")
    last_mm = pts[-1].get("micromarketRate")

    def pct(a: Optional[float], b: Optional[float]) -> Optional[float]:
        if a is None or b is None or a == 0:
            return None
        return ((b - a) / a) * 100.0

    return {
        "points": pts,
        "total_change_pct_locality": pct(first_loc, last_loc),
        "total_change_pct_micromarket": pct(first_mm, last_mm),
    }


def compute_exec_snapshot(payload: Dict[str, Any]) -> Dict[str, Any]:
    j1 = payload["sources"]["json1_locality"]
    j2 = payload["sources"]["json2_rates"]

    market_overview = j2.get("marketOverview") or {}
    price_trend = j2.get("priceTrend") or []
    rr_data = j1.get("ratingReviewData") or {}
    rental_stats = j1.get("rentalStats") or {}
    demand_supply = j1.get("demandSupply") or {}

    sale_units = ((demand_supply.get("sale") or {}).get("unitType")) or []
    rent_units = ((demand_supply.get("rent") or {}).get("unitType")) or []

    sale_total = sum_listings(sale_units)
    rent_total = sum_listings(rent_units)
    total = sale_total + rent_total

    donut = {
        "sale_count": sale_total,
        "rent_count": rent_total,
        "sale_pct": (sale_total / total * 100.0) if total else None,
        "rent_pct": (rent_total / total * 100.0) if total else None,
    }

    trend = compute_price_trend_summary(price_trend)
    sparkline = [{"x": p["quarterName"], "y": p["locationRate"]} for p in trend["points"]]

    # Demand-supply highlights (pick biggest absolute gap from each sale segment)
    def biggest_gap(items: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        g = compute_gap_table(items)
        valid = [r for r in g if isinstance(r.get("gap"), (int, float))]
        if not valid:
            return None
        return sorted(valid, key=lambda x: abs(x["gap"]), reverse=True)[0]

    sale = demand_supply.get("sale") or {}
    rent = demand_supply.get("rent") or {}

    highlights = {
        "sale_unitType_biggest_gap": biggest_gap(sale.get("unitType") or []),
        "sale_propertyType_biggest_gap": biggest_gap(sale.get("propertyType") or []),
        "sale_priceBand_biggest_gap": biggest_gap(sale.get("totalPrice_range") or []),
        "rent_unitType_biggest_gap": biggest_gap(rent.get("unitType") or []),
        "rent_propertyType_biggest_gap": biggest_gap(rent.get("propertyType") or []),
        "rent_priceBand_biggest_gap": biggest_gap(rent.get("totalPrice_range") or []),
    }

    return {
        "kpis": {
            "askingPrice": market_overview.get("askingPrice"),
            "registrationRate": market_overview.get("registrationRate"),
            "avgRentalRate": market_overview.get("avgRentalRate"),
            "rentalDescription": rental_stats.get("description"),
            "avgRating": rr_data.get("AvgRating"),
            "ratingCount": rr_data.get("RatingCount"),
            "reviewCount": rr_data.get("ReviewCount"),
        },
        "asking_price_sparkline": sparkline,
        "sale_vs_rent_supply_donut": donut,
        "highlights": highlights,
        "trend_summary": trend,
    }


def compute_market_snapshot(payload: Dict[str, Any]) -> Dict[str, Any]:
    j1 = payload["sources"]["json1_locality"]
    market_supply = j1.get("marketSupply") or {}
    rental_stats = j1.get("rentalStats") or {}

    hist = []
    for b in (market_supply.get("graphData") or []):
        hist.append({
            "bucketOrder": b.get("bucketOrder"),
            "bucketRange": b.get("bucketRange"),
            "saleCount": b.get("saleCount"),
        })
    hist = sorted(hist, key=lambda x: (x["bucketOrder"] if isinstance(x.get("bucketOrder"), int) else 999))

    rent_bhk = []
    for r in (rental_stats.get("rentalBHKStats") or []):
        avg_rupees = parse_inr_compact(r.get("avgRate"))
        rent_bhk.append({
            "unitType": r.get("unitType"),
            "avgRate_display": r.get("avgRate"),
            "avgRate_rupees": avg_rupees,
            "propertyType": r.get("propertyType"),
        })

    return {
        "marketSupply_histogram": hist,
        "rent_by_bhk": rent_bhk,
        "marketSupply_meta": {
            "listingsCount": market_supply.get("listingsCount"),
            "listingRate": market_supply.get("listingRate"),
            "description": market_supply.get("description"),
        },
        "rentalStats_meta": {
            "description": rental_stats.get("description"),
        },
    }


def compute_liveability(payload: Dict[str, Any]) -> Dict[str, Any]:
    j1 = payload["sources"]["json1_locality"]
    idx = j1.get("indices") or {}
    blocks = [
        ("Connectivity", idx.get("connectivity_index"), idx.get("connectivity_text")),
        ("Lifestyle", idx.get("lifestyle_index"), idx.get("lifestyle_text")),
        ("Education & Health", idx.get("educationhealth_index"), idx.get("educationhealth_text")),
        ("Livability", idx.get("livability_index"), idx.get("livability_text")),
    ]
    cards = []
    for name, score, html in blocks:
        cards.append({
            "name": name,
            "score": _safe_float(score),
            "bullets": html_ul_to_bullets(html),
        })
    return {"index_cards": cards}


def compute_nearby_comparison(payload: Dict[str, Any]) -> Dict[str, Any]:
    j2 = payload["sources"]["json2_rates"]
    loc_rates = j2.get("locationRates") or []
    rows = []
    for r in loc_rates:
        rows.append({
            "name": r.get("name"),
            "avgRate": _safe_float(r.get("avgRate")),
            "changePercentage": _safe_float(r.get("changePercentage")),
        })
    # sort by avgRate desc for bars
    rows_sorted = sorted([x for x in rows if x["avgRate"] is not None], key=lambda x: x["avgRate"], reverse=True)

    # ensure the main locality is included (meta.locality)
    main = payload.get("meta", {}).get("locality")
    if main:
        exists = any((x.get("name") == main) for x in rows_sorted)
        if not exists:
            # try case-insensitive match
            for x in rows:
                if (x.get("name") or "").strip().lower() == str(main).strip().lower():
                    rows_sorted.insert(0, x)
                    break

    top = rows_sorted[:10] if len(rows_sorted) > 10 else rows_sorted
    return {
        "comparison_rows_top": top,
        "bar_series": [{"label": x["name"], "value": x["avgRate"]} for x in top],
        "scatter_series": [{"x": x["avgRate"], "y": x["changePercentage"], "label": x["name"]} for x in top],
    }


def compute_demand_supply_segments(payload: Dict[str, Any], side: str) -> Dict[str, Any]:
    """
    side = "sale" or "rent"
    """
    j1 = payload["sources"]["json1_locality"]
    ds = (j1.get("demandSupply") or {}).get(side) or {}

    unit = compute_gap_table(ds.get("unitType") or [])
    ptype = compute_gap_table(ds.get("propertyType") or [])
    band = compute_gap_table(ds.get("totalPrice_range") or [])

    return {
        "unitType": {
            "table": unit,
            "top_gaps": top_gaps(unit, k=2),
        },
        "propertyType": {
            "table": ptype,
            "top_gaps": top_gaps(ptype, k=2),
        },
        "priceBand": {
            "table": band,
            "top_gaps": top_gaps(band, k=2),
        },
    }


def compute_propertytype_status(payload: Dict[str, Any]) -> Dict[str, Any]:
    j2 = payload["sources"]["json2_rates"]
    ptypes = []
    for p in (j2.get("propertyTypes") or []):
        ptypes.append({
            "propertyType": p.get("propertyType"),
            "avgPrice": _safe_float(p.get("avgPrice")),
            "changePercent": _safe_float(p.get("changePercent")),
        })
    pstatus = []
    for s in (j2.get("propertyStatus") or []):
        pstatus.append({
            "status": s.get("status"),
            "units": s.get("units"),
            "avgPrice": _safe_float(s.get("avgPrice")),
            "changePercent": _safe_float(s.get("changePercent")),
        })
    ptypes = sorted([x for x in ptypes if x["avgPrice"] is not None], key=lambda x: x["avgPrice"], reverse=True)
    pstatus = sorted([x for x in pstatus if x["avgPrice"] is not None], key=lambda x: x["avgPrice"], reverse=True)
    return {
        "propertyTypes_table": ptypes,
        "propertyStatus_table": pstatus,
        "propertyTypes_bar": [{"label": x["propertyType"], "value": x["avgPrice"], "change": x["changePercent"]} for x in ptypes],
        "propertyStatus_bar": [{"label": x["status"], "value": x["avgPrice"], "change": x["changePercent"], "units": x["units"]} for x in pstatus],
    }


def compute_top_projects(payload: Dict[str, Any]) -> Dict[str, Any]:
    j2 = payload["sources"]["json2_rates"]
    tp = j2.get("topProjects") or {}

    def norm_projects(arr: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        out = []
        for p in arr or []:
            out.append({
                "projectName": p.get("projectName"),
                "locality": p.get("locality"),
                "location": p.get("location"),
                "currentRate": _safe_float(p.get("currentRate")),
                "changePercentage": _safe_float(p.get("changePercentage")),
                "noOfTransactions": p.get("noOfTransactions"),
                "saleRentValue": _safe_float(p.get("saleRentValue")),
                "productUrl": p.get("productUrl"),
            })
        return out

    by_listing = norm_projects(((tp.get("byListingRates") or {}).get("projects")) or [])
    by_txn = norm_projects(((tp.get("byTransactions") or {}).get("projects")) or [])
    by_value = norm_projects(((tp.get("byValue") or {}).get("projects")) or [])

    # Sort for display
    by_listing = sorted(by_listing, key=lambda x: (x["currentRate"] if x["currentRate"] is not None else -1), reverse=True)
    by_txn = sorted(by_txn, key=lambda x: (x["noOfTransactions"] if isinstance(x["noOfTransactions"], (int, float)) else -1), reverse=True)
    by_value = sorted(by_value, key=lambda x: (x["saleRentValue"] if x["saleRentValue"] is not None else -1), reverse=True)

    return {
        "top_by_listing_rates": by_listing[:15],
        "top_by_transactions": by_txn[:15],
        "top_by_value": by_value[:15],
    }


def compute_registrations_developers(payload: Dict[str, Any]) -> Dict[str, Any]:
    j1 = payload["sources"]["json1_locality"]
    j2 = payload["sources"]["json2_rates"]

    reg1 = j1.get("govtRegistration") or {}
    reg2 = j2.get("govtRegistration") or {}

    # choose JSON-2 as primary, JSON-1 as supporting
    primary = reg2 if reg2 else reg1
    secondary = reg1 if primary is reg2 else reg2

    date_label = parse_date_range_end_label(primary.get("dateRange")) or parse_date_range_end_label(secondary.get("dateRange"))

    # developers by transactions
    devs = ((j2.get("topDevelopers") or {}).get("byTransactions") or {}).get("developers") or []
    rows = []
    total_top = 0
    for d in devs:
        cnt = d.get("noOfTransactions")
        cnt_i = int(cnt) if isinstance(cnt, (int, float)) else int(_safe_float(cnt) or 0)
        total_top += cnt_i
        rows.append({"developerName": d.get("developerName"), "noOfTransactions": cnt_i, "priority": d.get("priority")})

    # compute share within top list
    for r in rows:
        r["shareWithinTopPct"] = (r["noOfTransactions"] / total_top * 100.0) if total_top else None

    rows = sorted(rows, key=lambda x: x["noOfTransactions"], reverse=True)

    # recent transactions sample (masked values allowed)
    txns = j1.get("recentTransactions") or []
    sample = []
    for t in txns[:10]:
        sample.append({
            "propertyName": t.get("propertyName"),
            "locality": t.get("locality"),
            "area": t.get("area"),
            "registrationDate": t.get("registrationDate"),
            "assetType": t.get("assetType"),
            "transactionType": t.get("transactionType"),
            "ratePerSqft": t.get("ratePerSqft"),
            "saleRentValue": t.get("saleRentValue"),
        })

    return {
        "report_period_label": f"As of {date_label}" if date_label else None,
        "govtRegistration_primary": primary,
        "govtRegistration_secondary": secondary,
        "top_developers_by_transactions": rows[:15],
        "recent_transactions_sample": sample,
    }


def compute_reviews_conclusion(payload: Dict[str, Any]) -> Dict[str, Any]:
    j1 = payload["sources"]["json1_locality"]
    rr_data = j1.get("ratingReviewData") or {}
    rr = j1.get("ratingReview") or {}

    stars = []
    for s in (rr.get("ratingStarCount") or []):
        stars.append({"rating": s.get("Rating"), "count": s.get("Count")})
    stars = sorted(stars, key=lambda x: x["rating"], reverse=True)

    top_reviews = []
    for r in (rr.get("topReviews") or [])[:10]:
        desc = (r.get("Description") or "").strip()
        # keep short highlight for report table
        highlight = desc if len(desc) <= 220 else (desc[:217].rstrip() + "...")
        top_reviews.append({
            "name": r.get("Name"),
            "rating": r.get("Rating"),
            "createdOn": r.get("CreatedOn"),
            "persona": r.get("rating_user_persona"),
            "highlight": highlight,
            "positive": r.get("PositiveDesc"),
            "negative": r.get("NegativeDesc"),
        })

    pros = []
    for g in (rr.get("good") or [])[:8]:
        pros.append({"name": g.get("Name"), "percentage": _safe_float(g.get("Percentage"))})

    cons = []
    for b in (rr.get("bad") or [])[:8]:
        cons.append({"name": b.get("Name"), "percentage": _safe_float(b.get("Percentage"))})

    return {
        "rating_snapshot": {
            "avgRating": rr_data.get("AvgRating"),
            "ratingCount": rr_data.get("RatingCount"),
            "reviewCount": rr_data.get("ReviewCount"),
        },
        "star_distribution": stars,
        "top_reviews": top_reviews,
        "pros": pros,
        "cons": cons,
    }


def compute_report_period(payload: Dict[str, Any]) -> Optional[str]:
    """
    Determines report period label from:
      - json2 govtRegistration dateRange end
      - json1 govtRegistration dateRange end
      - recentTransactions max date
    """
    j1 = payload["sources"]["json1_locality"]
    j2 = payload["sources"]["json2_rates"]

    reg2 = (j2.get("govtRegistration") or {}).get("dateRange")
    reg1 = (j1.get("govtRegistration") or {}).get("dateRange")

    label = parse_date_range_end_label(reg2) or parse_date_range_end_label(reg1)
    if label:
        return f"As of {label}"

    # fallback to recent transaction max date
    txns = j1.get("recentTransactions") or []
    dates = []
    for t in txns:
        dt = parse_date_yyyy_mm_dd(t.get("registrationDate"))
        if dt:
            dates.append(dt)
    if dates:
        m = max(dates)
        return f"As of {m.strftime('%b %Y')}"
    return None


def compute_step2(payload: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Returns:
      - updated_payload (same architecture)
      - step2_quality_report
    """
    updated = dict(payload)  # shallow copy ok; we mutate per-page dicts
    step2_warnings: List[Dict[str, Any]] = []

    # Report period label goes to cover + page11 as well
    period = compute_report_period(payload)
    updated["page1_cover"]["computed"] = {"report_period_label": period}
    updated["page1_cover"]["narrative_inputs"] = {
        "tagline_template_vars": {
            "locality": payload.get("meta", {}).get("locality"),
            "city": payload.get("meta", {}).get("city"),
            "micromarket": payload.get("meta", {}).get("micromarket"),
            "report_period_label": period,
        }
    }

    # Page 2
    updated["page2_exec_snapshot"]["computed"] = compute_exec_snapshot(payload)
    updated["page2_exec_snapshot"]["narrative_inputs"] = {
        "llm_facts": {
            "trend_total_change_pct_locality": updated["page2_exec_snapshot"]["computed"]["trend_summary"]["total_change_pct_locality"],
            "trend_total_change_pct_micromarket": updated["page2_exec_snapshot"]["computed"]["trend_summary"]["total_change_pct_micromarket"],
            "biggest_sale_gap": updated["page2_exec_snapshot"]["computed"]["highlights"]["sale_unitType_biggest_gap"],
            "biggest_rent_gap": updated["page2_exec_snapshot"]["computed"]["highlights"]["rent_unitType_biggest_gap"],
        }
    }

    # Page 3
    updated["page3_liveability"]["computed"] = compute_liveability(payload)
    updated["page3_liveability"]["narrative_inputs"] = {
        "llm_facts": {"index_cards": updated["page3_liveability"]["computed"]["index_cards"]}
    }

    # Page 4
    updated["page4_market_snapshot"]["computed"] = compute_market_snapshot(payload)
    updated["page4_market_snapshot"]["narrative_inputs"] = {
        "llm_facts": {
            "marketSupply_meta": updated["page4_market_snapshot"]["computed"]["marketSupply_meta"],
            "rent_by_bhk": updated["page4_market_snapshot"]["computed"]["rent_by_bhk"],
        }
    }

    # Page 5
    j2 = payload["sources"]["json2_rates"]
    trend = compute_price_trend_summary(j2.get("priceTrend") or [])
    updated["page5_price_trend"]["computed"] = trend
    updated["page5_price_trend"]["narrative_inputs"] = {"llm_facts": trend}

    # Page 6
    comp = compute_nearby_comparison(payload)
    updated["page6_nearby_comparison"]["computed"] = comp
    updated["page6_nearby_comparison"]["narrative_inputs"] = {"llm_facts": {"comparison_rows_top": comp["comparison_rows_top"]}}

    # Page 7/8
    sale_seg = compute_demand_supply_segments(payload, "sale")
    rent_seg = compute_demand_supply_segments(payload, "rent")

    updated["page7_demand_supply_sale"]["computed"] = sale_seg
    updated["page7_demand_supply_sale"]["narrative_inputs"] = {"llm_facts": sale_seg}

    updated["page8_demand_supply_rent"]["computed"] = rent_seg
    updated["page8_demand_supply_rent"]["narrative_inputs"] = {"llm_facts": rent_seg}

    # Page 9
    ps = compute_propertytype_status(payload)
    updated["page9_propertytype_status"]["computed"] = ps
    updated["page9_propertytype_status"]["narrative_inputs"] = {"llm_facts": ps}

    # Page 10
    tp = compute_top_projects(payload)
    updated["page10_top_projects"]["computed"] = tp
    updated["page10_top_projects"]["narrative_inputs"] = {"llm_facts": tp}

    # Page 11
    reg = compute_registrations_developers(payload)
    updated["page11_registrations_developers"]["computed"] = reg
    updated["page11_registrations_developers"]["narrative_inputs"] = {"llm_facts": reg}

    # Warn if topDevelopers.byValue absent (your step1 already flagged this)
    top_dev = (payload["sources"]["json2_rates"].get("topDevelopers") or {})
    if "byValue" not in top_dev:
        step2_warnings.append({
            "level": "warning",
            "code": "missing_optional_block",
            "message": "JSON-2 topDevelopers.byValue is missing; Page 11 will render developers-by-value as 'Not available'.",
            "path": "sources.json2_rates.topDevelopers.byValue",
        })

    # Page 12
    rev = compute_reviews_conclusion(payload)
    updated["page12_reviews_conclusion"]["computed"] = rev
    updated["page12_reviews_conclusion"]["narrative_inputs"] = {
        "llm_facts": {
            "rating_snapshot": rev["rating_snapshot"],
            "pros": rev["pros"],
            "cons": rev["cons"],
            "trend_total_change_pct_locality": trend.get("total_change_pct_locality"),
            "sale_top_under_supply": sale_seg["unitType"]["top_gaps"]["under_supplied"],
            "rent_top_under_supply": rent_seg["unitType"]["top_gaps"]["under_supplied"],
        }
    }

    summary = {
        "computed_summary": {
            "page2_sparkline_points": len(updated["page2_exec_snapshot"]["computed"]["asking_price_sparkline"]),
            "page4_histogram_buckets": len(updated["page4_market_snapshot"]["computed"]["marketSupply_histogram"]),
            "page4_rent_bhk_rows": len(updated["page4_market_snapshot"]["computed"]["rent_by_bhk"]),
            "page6_comparison_rows": len(updated["page6_nearby_comparison"]["computed"]["comparison_rows_top"]),
            "page10_top_by_listing": len(updated["page10_top_projects"]["computed"]["top_by_listing_rates"]),
            "page12_top_reviews": len(updated["page12_reviews_conclusion"]["computed"]["top_reviews"]),
        }
    }

    quality = {
        "stage": "step2_compute",
        "warnings": step2_warnings,
        "summary": summary,
    }

    return updated, quality