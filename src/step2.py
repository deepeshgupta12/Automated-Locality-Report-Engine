from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict

from src.transform.compute_pages import compute_step2


def _read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Input JSON not found: {path}")
    obj = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        raise ValueError("Input payload must be a JSON object")
    return obj


def _write_json(path: Path, obj: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", default="out/report_payload.json", help="Step1 payload path")
    ap.add_argument("--outdir", default="out", help="Output directory")
    args = ap.parse_args()

    inp_path = Path(args.inp)
    outdir = Path(args.outdir)

    payload = _read_json(inp_path)
    step2_payload, step2_quality = compute_step2(payload)

    _write_json(outdir / "report_payload_step2.json", step2_payload)
    _write_json(outdir / "quality_report_step2.json", step2_quality)

    print("Done.")
    print(f"Step2 payload: {outdir / 'report_payload_step2.json'}")
    print(f"Step2 quality report: {outdir / 'quality_report_step2.json'}")

    if step2_quality.get("warnings"):
        print(f"Warnings: {len(step2_quality['warnings'])} (see quality_report_step2.json)")
    else:
        print("No Step2 warnings.")


if __name__ == "__main__":
    main()