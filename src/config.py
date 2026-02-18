from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppConfig:
    project_root: Path
    data_dir: Path
    out_dir: Path

    default_locality_json: Path
    default_rates_json: Path

    report_payload_path: Path
    quality_report_path: Path


def load_config() -> AppConfig:
    root = Path(__file__).resolve().parents[1]  # locality-report-product/
    data_dir = root / "data"
    out_dir = root / "out"

    return AppConfig(
        project_root=root,
        data_dir=data_dir,
        out_dir=out_dir,
        default_locality_json=data_dir / "Andheri East Locality.json",
        default_rates_json=data_dir / "Andheri East Property Rates.json",
        report_payload_path=out_dir / "report_payload.json",
        quality_report_path=out_dir / "quality_report.json",
    )