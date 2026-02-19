from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict

from src.llm.openai_client import call_structured
from src.llm.schema import NARRATIVE_SCHEMA
from src.render.pdf import render_pdf


def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, obj: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def build_llm_input(payload: Dict[str, Any]) -> str:
    """
    Provide only the minimum facts needed, to reduce hallucination risk.
    We pull only page-wise inputs already in the payload.
    """
    meta = payload.get("meta", {}) or {}

    def pick(page_key: str) -> Dict[str, Any]:
        p = payload.get(page_key, {}) or {}
        return {
            "data": p.get("data", {}) or {},
            "computed": p.get("computed", {}) or {},
            "narrative_inputs": p.get("narrative_inputs", {}) or {},
        }

    bundle = {
        "meta": meta,
        "page2_exec_snapshot": pick("page2_exec_snapshot"),
        "page3_liveability": pick("page3_liveability"),
        "page4_market_snapshot": pick("page4_market_snapshot"),
        "page5_price_trend": pick("page5_price_trend"),
        "page6_nearby_comparison": pick("page6_nearby_comparison"),
        "page7_demand_supply_sale": pick("page7_demand_supply_sale"),
        "page8_demand_supply_rent": pick("page8_demand_supply_rent"),
        "page9_propertytype_status": pick("page9_propertytype_status"),
        "page10_top_projects": pick("page10_top_projects"),
        "page11_registrations_developers": pick("page11_registrations_developers"),
        "page12_reviews_conclusion": pick("page12_reviews_conclusion"),
    }
    return json.dumps(bundle, ensure_ascii=False, indent=2)


INSTRUCTIONS = """You write concise narrative copy for a locality report.

Hard rules:
- Use ONLY the provided JSON facts. Do NOT add outside knowledge.
- If a claim is not directly supported by the JSON, do not write it.
- No fluff, no marketing hype, no emojis.
- Keep sentences short and factual.
- Avoid absolute language (e.g., 'best', 'always').

Missing-data rule:
- If the JSON does not contain enough evidence to write meaningful copy for a field, return an empty string "" for that field.

Output rules:
- Return JSON matching the provided schema exactly.
- page2_exec_snapshot.takeaways: prefer a short HTML list (<ul><li>..</li></ul>) with up to 4 bullets.
- page4_market_snapshot.narrative: 2–4 short sentences summarizing:
  (a) buy-side supply distribution description (marketSupply.description / graphData if present)
  (b) rent-side avg rent by unit type (rentalStats / rentalBHKStats if present)
  (c) avoid numbers unless they are present in JSON.
- Other narrative fields: 2–5 short sentences, plain text is fine (HTML allowed but optional).
"""


def _attach_narratives(payload: Dict[str, Any], llm: Dict[str, Any]) -> None:
    """
    Store narratives in locations that src/render/pdf.py can actually read.
    - payload["narratives"][page_key][field]
    - payload[page_key]["computed"]["narratives"][field] (backup)
    """
    payload.setdefault("narratives", {})
    for page_key, obj in llm.items():
        if not isinstance(obj, dict):
            continue

        # primary (global)
        payload["narratives"][page_key] = obj

        # backup (page-local)
        page = payload.setdefault(page_key, {})
        computed = page.setdefault("computed", {})
        computed.setdefault("narratives", {})
        computed["narratives"].update(obj)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True, help="Path to report_payload_step3.json")
    ap.add_argument("--outdir", required=True, help="Output directory")
    ap.add_argument("--model", default=None, help="Optional model override (else OPENAI_MODEL/env)")
    args = ap.parse_args()

    inp = Path(args.inp).expanduser()
    outdir = Path(args.outdir).expanduser()
    outdir.mkdir(parents=True, exist_ok=True)

    payload = _read_json(inp)
    user_input = build_llm_input(payload)

    llm = call_structured(
        instructions=INSTRUCTIONS,
        user_input=user_input,
        schema=NARRATIVE_SCHEMA,
        model=args.model,
    )

    _attach_narratives(payload, llm)

    step5_payload = outdir / "report_payload_step5.json"
    _write_json(step5_payload, payload)

    locality = (payload.get("meta", {}) or {}).get("locality", "Locality")
    out_pdf = outdir / f"{locality} Locality Report - Final.pdf"
    render_pdf(payload, out_pdf)

    print("Done.")
    print(f"Step5 payload: {step5_payload}")
    print(f"Final PDF: {out_pdf}")


if __name__ == "__main__":
    main()