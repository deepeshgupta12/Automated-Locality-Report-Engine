from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


def _get(obj: Any, path: str) -> Any:
    # Same semantics as transform._get (kept local to avoid circular deps)
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
        if "[" in part and part.endswith("]"):
            base = part[: part.index("[")]
            idx_str = part[part.index("[") + 1 : -1]
            try:
                idx = int(idx_str)
            except Exception:
                return None
            if base:
                if not isinstance(cur, dict) or base not in cur:
                    return None
                cur = cur[base]
            if not isinstance(cur, list) or idx < 0 or idx >= len(cur):
                return None
            cur = cur[idx]
        else:
            if not isinstance(cur, dict) or part not in cur:
                return None
            cur = cur[part]
    return cur


@dataclass(frozen=True)
class RequiredKey:
    label: str
    path: str
    severity: str  # "error" | "warning"


def _is_nonempty_list(v: Any) -> bool:
    return isinstance(v, list) and len(v) > 0


def validate_inputs(json1: Dict[str, Any], json2: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validates raw JSON inputs against *real* key paths in your two files.
    Produces a quality report with errors/warnings.
    """
    req: List[RequiredKey] = [
        # -------------------
        # JSON-1 (Locality)
        # -------------------
        RequiredKey("JSON-1: locality name", "data.localityOverviewData.name", "error"),
        RequiredKey("JSON-1: city name", "data.localityOverviewData.cityName", "error"),
        RequiredKey("JSON-1: micromarket label", "data.localityOverviewData.dotcomLocationName", "error"),
        RequiredKey("JSON-1: rating avg", "data.localityOverviewData.ratingReviewData.AvgRating", "error"),
        RequiredKey("JSON-1: rating count", "data.localityOverviewData.ratingReviewData.RatingCount", "error"),
        RequiredKey("JSON-1: review count", "data.localityOverviewData.ratingReviewData.ReviewCount", "error"),

        # demandSupply (you explicitly confirmed it exists)
        RequiredKey("JSON-1: demandSupply.sale.unitType", "data.demandSupply.sale.unitType", "error"),
        RequiredKey("JSON-1: demandSupply.sale.propertyType", "data.demandSupply.sale.propertyType", "error"),
        RequiredKey("JSON-1: demandSupply.sale.totalPrice_range", "data.demandSupply.sale.totalPrice_range", "error"),
        RequiredKey("JSON-1: demandSupply.rent.unitType", "data.demandSupply.rent.unitType", "error"),
        RequiredKey("JSON-1: demandSupply.rent.propertyType", "data.demandSupply.rent.propertyType", "error"),
        RequiredKey("JSON-1: demandSupply.rent.totalPrice_range", "data.demandSupply.rent.totalPrice_range", "error"),

        # Market snapshot blocks (under insightsData)
        RequiredKey("JSON-1: govtRegistration", "data.insightsData.govtRegistration", "error"),
        RequiredKey("JSON-1: marketSupply", "data.insightsData.marketSupply", "error"),
        RequiredKey("JSON-1: rentalStats", "data.insightsData.rentalStats", "error"),
        RequiredKey("JSON-1: recentTransactions", "data.insightsData.recentTransactions", "warning"),  # allowed to be missing

        # Indices
        RequiredKey("JSON-1: indices", "data.indices", "error"),

        # Reviews for Page 12 (these exist in your payload; allow warning if absent)
        RequiredKey("JSON-1: ratingReview.ratingStarCount", "data.ratingReview.ratingStarCount", "warning"),
        RequiredKey("JSON-1: ratingReview.topReviews", "data.ratingReview.topReviews", "warning"),

        # -------------------
        # JSON-2 (Rates)
        # -------------------
        RequiredKey("JSON-2: marketOverview", "result.marketOverview", "error"),
        RequiredKey("JSON-2: priceTrend", "result.priceTrend", "error"),
        RequiredKey("JSON-2: locationRates", "result.locationRates", "error"),
        RequiredKey("JSON-2: propertyTypes", "result.propertyTypes", "error"),
        RequiredKey("JSON-2: propertyStatus", "result.propertyStatus", "error"),
        RequiredKey("JSON-2: topProjects", "result.topProjects", "error"),
        RequiredKey("JSON-2: govtRegistration", "result.govtRegistration", "error"),
        RequiredKey("JSON-2: topDevelopers.byTransactions", "result.topDevelopers.byTransactions", "error"),
        # This is in your architecture but NOT present in your sample JSON-2 (so warning, not error)
        RequiredKey("JSON-2: topDevelopers.byValue", "result.topDevelopers.byValue", "warning"),
    ]

    errors: List[Dict[str, Any]] = []
    warnings: List[Dict[str, Any]] = []

    for r in req:
        v = _get(json1 if r.path.startswith("data.") else json2, r.path)

        missing = v is None
        # for lists, treat empty list as missing (for the required list blocks)
        if isinstance(v, list) and len(v) == 0:
            missing = True

        if missing:
            item = {
                "level": r.severity,
                "code": "missing_required_key",
                "message": f"Missing required key: {r.label}",
                "path": r.path,
            }
            if r.severity == "error":
                errors.append(item)
            else:
                warnings.append(item)

    return {
        "issue_count": len(errors) + len(warnings),
        "errors": errors,
        "warnings": warnings,
    }