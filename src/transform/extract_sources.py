from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple


def _get(obj: Any, path: str) -> Any:
    """
    Safe path getter supporting:
      - dot paths: a.b.c
      - list indices: a.b[0].c
    Returns None if any segment is missing.
    """
    cur = obj
    if not path:
        return cur

    parts: List[str] = []
    buf = ""
    i = 0
    while i < len(path):
        ch = path[i]
        if ch == ".":
            if buf:
                parts.append(buf)
                buf = ""
            i += 1
            continue
        buf += ch
        i += 1
    if buf:
        parts.append(buf)

    for part in parts:
        # handle bracket segments inside this part, e.g. ratingOverview[0]
        segs: List[Tuple[str, Optional[int]]] = []
        s = part
        while True:
            if "[" in s and s.endswith("]"):
                base = s[: s.index("[")]
                idx_str = s[s.index("[") + 1 : -1]
                try:
                    idx = int(idx_str)
                except Exception:
                    return None
                segs.append((base, idx))
                break
            else:
                segs.append((s, None))
                break

        for key, idx in segs:
            if key:
                if not isinstance(cur, dict) or key not in cur:
                    return None
                cur = cur[key]
            if idx is not None:
                if not isinstance(cur, list) or idx < 0 or idx >= len(cur):
                    return None
                cur = cur[idx]
    return cur


def extract_sources(json1: Dict[str, Any], json2: Dict[str, Any]) -> Dict[str, Any]:
    """
    Produces canonical 'sources' blocks used by the 12-page architecture.
    IMPORTANT: No assumptions; only extract what exists.
    """
    # JSON-1 root
    j1 = _get(json1, "data") or {}

    # JSON-2 root: your file has keys: code/status/result/data(None)
    j2 = _get(json2, "result") or {}

    # ---- JSON-1 canonical blocks ----
    localityOverviewData = _get(j1, "localityOverviewData")
    demandSupply = _get(j1, "demandSupply")
    indices = _get(j1, "indices")

    # insightsData contains govtRegistration/marketSupply/rentalStats/recentTransactions/nearByLocations/priceTrend
    insightsData = _get(j1, "insightsData") or {}
    govtRegistration_1 = _get(insightsData, "govtRegistration")
    marketSupply = _get(insightsData, "marketSupply")
    rentalStats = _get(insightsData, "rentalStats")
    recentTransactions = _get(insightsData, "recentTransactions")

    # ratingReviewData is nested inside localityOverviewData in your JSON-1
    ratingReviewData = _get(localityOverviewData, "ratingReviewData") if localityOverviewData else None

    # reviews section for Page 12
    ratingReview = _get(j1, "ratingReview")

    # ---- JSON-2 canonical blocks ----
    marketOverview = _get(j2, "marketOverview")
    priceTrend = _get(j2, "priceTrend")
    locationRates = _get(j2, "locationRates")
    propertyTypes = _get(j2, "propertyTypes")
    propertyStatus = _get(j2, "propertyStatus")
    topProjects = _get(j2, "topProjects")
    govtRegistration_2 = _get(j2, "govtRegistration")
    topDevelopers = _get(j2, "topDevelopers")

    return {
        "json1_locality": {
            "localityOverviewData": localityOverviewData,
            "ratingReviewData": ratingReviewData,
            "demandSupply": demandSupply,
            "govtRegistration": govtRegistration_1,
            "marketSupply": marketSupply,
            "rentalStats": rentalStats,
            "recentTransactions": recentTransactions,
            "indices": indices,
            "ratingReview": ratingReview,
        },
        "json2_rates": {
            "details": _get(j2, "details"),  # metadata only
            "marketOverview": marketOverview,
            "priceTrend": priceTrend,
            "locationRates": locationRates,
            "propertyTypes": propertyTypes,
            "propertyStatus": propertyStatus,
            "topProjects": topProjects,
            "govtRegistration": govtRegistration_2,
            "topDevelopers": topDevelopers,
        },
    }