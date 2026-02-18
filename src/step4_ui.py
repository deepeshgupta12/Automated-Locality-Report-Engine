from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any, Dict


def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, obj: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def _copy_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True, help="Path to report_payload_step3.json")
    ap.add_argument("--ui", dest="ui_dir", required=True, help="Path to ui folder (Lovable app)")
    ap.add_argument("--copy-charts", action="store_true", help="Also copy chart PNGs into ui/public/charts/")
    args = ap.parse_args()

    inp = Path(args.inp).expanduser().resolve()
    ui = Path(args.ui_dir).expanduser().resolve()

    if not inp.exists():
        raise SystemExit(f"Input not found: {inp}")
    if not (ui / "package.json").exists():
        raise SystemExit(f"UI folder does not look like a Vite app (missing package.json): {ui}")

    payload = _read_json(inp)

    # 1) Write payload into UI as a compile-time import (what Lovable currently expects)
    ui_data_path = ui / "src" / "data" / "report_payload.json"
    _write_json(ui_data_path, payload)

    # 2) Also write into /public for runtime fetch/debug (optional but handy)
    public_payload_path = ui / "public" / "report_payload.json"
    _write_json(public_payload_path, payload)

    # 3) Optionally copy PNG charts for future use
    copied = []
    if args.copy_charts:
        charts = payload.get("charts") or {}
        for _, p in charts.items():
            src = Path(p)
            # support both absolute and repo-relative paths
            if not src.is_absolute():
                src = (inp.parent / src).resolve()

            if src.exists() and src.suffix.lower() == ".png":
                dst = ui / "public" / "charts" / src.name
                _copy_file(src, dst)
                copied.append(str(dst))

    print("Done.")
    print(f"Wrote UI data JSON: {ui_data_path}")
    print(f"Wrote UI public JSON: {public_payload_path}")
    if args.copy_charts:
        print(f"Copied charts: {len(copied)} file(s)")


if __name__ == "__main__":
    main()