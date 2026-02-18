from __future__ import annotations

import re
from typing import Optional


def parse_inr_compact(value: object) -> Optional[float]:
    """
    Parses values like:
      "₹ 25.7 K" -> 25700
      "₹ 1.2 L"  -> 120000
      "₹ 3.5 Cr" -> 35000000
      "30108" or 30108 -> 30108

    Returns rupees as float or None if unparseable.
    """
    if value is None:
        return None

    if isinstance(value, (int, float)):
        return float(value)

    s = str(value).strip()
    if not s:
        return None

    # Remove currency symbol and commas
    s = s.replace("₹", "").replace(",", "").strip()

    # Match optional unit suffix (K/L/Cr)
    m = re.match(r"^([0-9]*\.?[0-9]+)\s*([A-Za-z]+)?$", s)
    if not m:
        # Try extracting a number from mixed strings
        m2 = re.search(r"([0-9]*\.?[0-9]+)", s)
        if not m2:
            return None
        num = float(m2.group(1))
        return num

    num = float(m.group(1))
    unit = (m.group(2) or "").lower()

    if unit in ("k",):
        return num * 1_000
    if unit in ("l", "lac", "lakh", "lakhs"):
        return num * 100_000
    if unit in ("cr", "crore", "crores"):
        return num * 10_000_000

    return num


def format_inr_short(rupees: Optional[float]) -> str:
    """
    Formats rupees into a compact readable label:
      25700 -> "₹ 25.7K"
      120000 -> "₹ 1.2L"
      35000000 -> "₹ 3.5Cr"
    """
    if rupees is None:
        return "NA"
    r = float(rupees)
    if r >= 10_000_000:
        return f"₹ {r/10_000_000:.1f}Cr"
    if r >= 100_000:
        return f"₹ {r/100_000:.1f}L"
    if r >= 1_000:
        return f"₹ {r/1_000:.1f}K"
    return f"₹ {r:.0f}"