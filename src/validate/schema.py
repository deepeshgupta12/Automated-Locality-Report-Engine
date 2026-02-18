from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, Union


Json = Dict[str, Any]


@dataclass
class Issue:
    level: str  # "error" | "warn"
    code: str
    message: str
    path: str


def _parse_path(path: str) -> List[Union[str, int]]:
    """
    Supports paths like:
      "a.b.c"
      "a.b[0].c"
      "a[2]"
    """
    tokens: List[Union[str, int]] = []
    i = 0
    buf = ""
    while i < len(path):
        ch = path[i]
        if ch == ".":
            if buf:
                tokens.append(buf)
                buf = ""
            i += 1
            continue
        if ch == "[":
            if buf:
                tokens.append(buf)
                buf = ""
            j = path.find("]", i)
            if j == -1:
                raise ValueError(f"Unclosed bracket in path: {path}")
            idx_str = path[i + 1 : j].strip()
            if not idx_str.isdigit():
                raise ValueError(f"Non-integer index in path: {path}")
            tokens.append(int(idx_str))
            i = j + 1
            continue
        buf += ch
        i += 1
    if buf:
        tokens.append(buf)
    return tokens


def get_at_path(obj: Any, path: str) -> Tuple[bool, Any]:
    """
    Returns: (found, value)
    """
    try:
        tokens = _parse_path(path)
    except Exception:
        return False, None

    cur = obj
    for t in tokens:
        if isinstance(t, int):
            if not isinstance(cur, list) or t < 0 or t >= len(cur):
                return False, None
            cur = cur[t]
        else:
            if not isinstance(cur, dict) or t not in cur:
                return False, None
            cur = cur[t]
    return True, cur


def type_name(v: Any) -> str:
    if v is None:
        return "null"
    return type(v).__name__


def validate_required_paths(
    root: Json,
    required: List[Tuple[str, Union[type, Tuple[type, ...]]]],
    *,
    label: str
) -> List[Issue]:
    issues: List[Issue] = []
    for path, expected_type in required:
        found, value = get_at_path(root, path)
        if not found:
            issues.append(Issue(
                level="error",
                code="missing_required_key",
                message=f"Missing required key for {label}: {path}",
                path=path
            ))
            continue
        if expected_type is not Any and expected_type is not None:
            # Allow None only if explicitly included in tuple
            if not isinstance(value, expected_type):
                issues.append(Issue(
                    level="error",
                    code="type_mismatch",
                    message=f"Type mismatch at {path}: expected {expected_type}, got {type_name(value)}",
                    path=path
                ))
    return issues


def validate_optional_paths(
    root: Json,
    optional: List[Tuple[str, Union[type, Tuple[type, ...]]]],
    *,
    label: str
) -> List[Issue]:
    """
    Optional: missing => warn, type mismatch => warn
    """
    issues: List[Issue] = []
    for path, expected_type in optional:
        found, value = get_at_path(root, path)
        if not found:
            issues.append(Issue(
                level="warn",
                code="missing_optional_key",
                message=f"Missing optional key for {label}: {path}",
                path=path
            ))
            continue
        if expected_type is not Any and expected_type is not None:
            if not isinstance(value, expected_type):
                issues.append(Issue(
                    level="warn",
                    code="type_mismatch_optional",
                    message=f"Type mismatch at {path}: expected {expected_type}, got {type_name(value)}",
                    path=path
                ))
    return issues


def safe_number(v: Any) -> Optional[float]:
    """
    Converts numeric strings to float where safe.
    Keeps None as None.
    Returns None if cannot parse.
    """
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        s = v.strip()
        # Attempt plain float conversion (no currency parsing here)
        try:
            return float(s.replace(",", ""))
        except Exception:
            return None
    return None


def compute_gap_items(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    For demandSupply arrays where each item has:
      name, listing, demandPercent, supplyPercent
    Adds:
      gap = demandPercent - supplyPercent
    """
    out: List[Dict[str, Any]] = []
    for it in items:
        dp = safe_number(it.get("demandPercent"))
        sp = safe_number(it.get("supplyPercent"))
        gap = None
        if dp is not None and sp is not None:
            gap = dp - sp
        out.append({**it, "gap": gap})
    return out