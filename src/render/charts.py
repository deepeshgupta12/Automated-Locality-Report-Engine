from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import matplotlib.pyplot as plt

from src.utils.money import parse_inr_compact


@dataclass(frozen=True)
class ChartResult:
    name: str
    path: str


def _save_fig(out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close()


def chart_price_trend(points: List[Dict[str, Any]], out_path: Path) -> None:
    # Expect points in newest->oldest; plot oldest->newest for natural trend.
    pts = list(reversed(points))
    x = [p.get("quarterName", "") for p in pts]
    y1 = [float(p.get("locationRate") or 0.0) for p in pts]
    y2 = [float(p.get("micromarketRate") or 0.0) for p in pts]

    plt.figure(figsize=(8, 3.5))
    plt.plot(x, y1, marker="o")
    plt.plot(x, y2, marker="o")
    plt.title("Asking Price Trend (Locality vs Micro-market)")
    plt.xlabel("Quarter")
    plt.ylabel("Rate (₹/sq ft)")
    plt.grid(True, alpha=0.2)
    plt.legend(["Locality", "Micro-market"])
    _save_fig(out_path)


def chart_histogram_buckets(graph_data: List[Dict[str, Any]], out_path: Path) -> None:
    # Bars by bucketRange with saleCount
    buckets = [d.get("bucketRange", "") for d in graph_data]
    counts = [int(d.get("saleCount") or 0) for d in graph_data]

    plt.figure(figsize=(8, 3.5))
    plt.bar(buckets, counts)
    plt.title("Market Supply Distribution (Listing Rate Buckets)")
    plt.xlabel("₹/sq ft bucket")
    plt.ylabel("Listings")
    plt.xticks(rotation=20, ha="right")
    plt.grid(True, axis="y", alpha=0.2)
    _save_fig(out_path)


def chart_rent_by_bhk(rental_bhk_stats: List[Dict[str, Any]], out_path: Path) -> None:
    labels = [d.get("unitType", "") for d in rental_bhk_stats]
    values = [parse_inr_compact(d.get("avgRate")) or 0.0 for d in rental_bhk_stats]

    plt.figure(figsize=(8, 3.5))
    plt.bar(labels, values)
    plt.title("Average Monthly Rent by Unit Type")
    plt.xlabel("Unit Type")
    plt.ylabel("Monthly rent (₹)")
    plt.grid(True, axis="y", alpha=0.2)
    _save_fig(out_path)


def chart_nearby_rates(location_rates: List[Dict[str, Any]], out_path: Path, max_n: int = 10) -> None:
    # Sort by avgRate desc and show top N
    rows = []
    for r in location_rates:
        name = r.get("name") or ""
        rate = r.get("avgRate")
        if rate is None:
            continue
        rows.append((name, float(rate)))
    rows.sort(key=lambda x: x[1], reverse=True)
    rows = rows[:max_n]

    names = [x[0] for x in rows]
    vals = [x[1] for x in rows]

    plt.figure(figsize=(8, 4.0))
    plt.barh(names[::-1], vals[::-1])
    plt.title("Locality vs Nearby Localities (Avg Rate)")
    plt.xlabel("Rate (₹/sq ft)")
    plt.grid(True, axis="x", alpha=0.2)
    _save_fig(out_path)


def chart_dual_gap_bars(
    items: List[Dict[str, Any]],
    out_path: Path,
    title: str,
    max_n: int = 12,
) -> None:
    # demandPercent vs supplyPercent grouped bars
    trimmed = items[:max_n]
    labels = [i.get("name", "") for i in trimmed]
    demand = [float(i.get("demandPercent") or 0.0) for i in trimmed]
    supply = [float(i.get("supplyPercent") or 0.0) for i in trimmed]

    x = list(range(len(labels)))
    width = 0.4

    plt.figure(figsize=(9, 3.8))
    plt.bar([v - width / 2 for v in x], demand, width=width)
    plt.bar([v + width / 2 for v in x], supply, width=width)
    plt.title(title)
    plt.xlabel("Segment")
    plt.ylabel("Share (%)")
    plt.xticks(x, labels, rotation=20, ha="right")
    plt.legend(["Demand %", "Supply %"])
    plt.grid(True, axis="y", alpha=0.2)
    _save_fig(out_path)


def chart_simple_bar(
    labels: List[str],
    values: List[float],
    out_path: Path,
    title: str,
    xlabel: str,
    ylabel: str,
    rotate: bool = True,
) -> None:
    plt.figure(figsize=(9, 3.8))
    plt.bar(labels, values)
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    if rotate:
        plt.xticks(rotation=20, ha="right")
    plt.grid(True, axis="y", alpha=0.2)
    _save_fig(out_path)