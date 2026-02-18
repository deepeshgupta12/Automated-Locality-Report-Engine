# 🏙️ Automated Locality Report Engine

Generate a **full locality report** (data → charts → LLM narratives → PDF + Lovable UI) from two JSON feeds (Locality + Property Rates).  
Built to be **repeatable for any locality** (e.g., Andheri East ✅, Malad East ✅) without code changes — just swap input JSONs and the polygon/map asset.

---

## 🎯 Problem Statement

Real-estate locality insights are often scattered across multiple data sources and are hard to package into a consistent, shareable report.

Teams typically need to:
- merge multiple locality datasets,
- compute/derive key indicators,
- render charts and structured tables,
- write human-readable narratives, and
- ship the same content to **PDF + UI**.

Doing this manually is slow, inconsistent, and doesn’t scale across hundreds of localities.

---

## ✅ Solution

This repo provides an **automated pipeline** that:

1. **Merges + validates** the two input JSONs into a canonical `report_payload.json`
2. Generates **computed fields + chart PNGs** into `report_payload_step3.json`
3. Uses **OpenAI Structured Outputs** to generate **grounded narratives** (no hallucination)
4. Produces a **final PDF** via ReportLab
5. Wires the same payload into a **Lovable (Vite/React) UI**, so the report can be viewed in-browser
6. Exposes a **Download PDF** CTA (single tall, scroll-like page if server-side render is enabled)

---

## 🧭 Key Objectives

- **Scalable locality reporting**: generate the same report structure for any locality input
- **Consistency**: same source-of-truth payload powers both PDF + UI
- **Grounded narratives**: LLM copy strictly uses provided JSON facts (Structured Outputs)
- **No manual formatting**: charts/tables/narratives are auto-rendered
- **Production-friendly**: clear step-based pipeline, deterministic artifacts in `out/`

---

## 🧱 Tech Stack

### Backend / Pipeline
- 🐍 Python 3.10+
- 📦 Pydantic (validation)
- 📊 Matplotlib (charts)
- 🧾 ReportLab (PDF rendering)
- 🧠 OpenAI SDK (Structured Outputs / Responses API)
- 🧰 python-dotenv (env management)

### Frontend (Lovable UI)
- ⚛️ React + TypeScript
- ⚡ Vite
- 🎨 TailwindCSS (UI styling)
- 🧩 Componentized report sections

---

## 🗂️ Repo Structure (high level)

```
.
├── data/                          # input JSONs per locality
├── out/                           # generated artifacts (payloads, charts, PDFs)
├── src/
│   ├── main.py                    # Step 1: merge + validate → report_payload.json
│   ├── step3_*.py                 # Step 3: charts + computed → report_payload_step3.json
│   ├── step4_ui.py                # Step 4: copy payload into ui/
│   ├── step5_llm.py               # Step 5.1: LLM narratives + final PDF
│   ├── llm/
│   │   └── openai_client.py       # OpenAI structured call wrapper
│   └── render/
│       └── pdf.py                 # PDF renderer (tables + narrative printing)
└── ui/
    ├── src/
    │   ├── data/report_payload.json
    │   ├── lib/reportData.ts
    │   └── components/report/*    # report sections (Summary, Trend, DemandSupply, etc.)
    └── public/
        ├── report_payload.json
        └── charts/
```

> Note: The exact filename of `step3_*` depends on your repo (it is the script that produces `out/report_payload_step3.json`).

---

## 🧪 How to Run (End-to-End)

### 0) Setup

```bash
cd locality-report-product
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

### 1) Step 1 — Merge + Validate

```bash
python -m src.main   --json1 "data/Andheri East Locality.json"   --json2 "data/Andheri East Property Rates.json"   --out "out"
```

Outputs:
- `out/report_payload.json`
- `out/quality_report.json`

---

### 2) Step 3 — Charts + Computed Payload

Run the Step 3 module in your repo that generates `out/report_payload_step3.json`, e.g.:

```bash
python -m src.step3_charts   --in "out/report_payload.json"   --outdir "out"
```

Outputs:
- `out/report_payload_step3.json`
- chart PNGs referenced inside payload (typically `out/charts/*.png`)

---

### 3) Step 5.1 — LLM Narrative Generation (OpenAI Structured Outputs)

Set env vars:

```bash
export OPENAI_API_KEY="YOUR_KEY"
export OPENAI_MODEL="gpt-4.1-mini"
```

Run:

```bash
python -m src.step5_llm   --in "out/report_payload_step3.json"   --outdir "out"
```

Outputs:
- `out/report_payload_step5.json` (payload now includes `narratives`)
- `out/<Locality> Locality Report - Final.pdf`

---

### 4) Step 5.3 — Wire Step 5 Payload into UI (so narratives show)

```bash
python -m src.step4_ui   --in "out/report_payload_step5.json"   --ui "ui"   --copy-charts
```

Writes:
- `ui/src/data/report_payload.json`
- `ui/public/report_payload.json`
- `ui/public/charts/`

---

### 5) Run UI

```bash
cd ui
npm install
npm run dev -- --host 0.0.0.0 --port 8080
```

Open:
- http://localhost:8080

---

## 🧠 LLM Narrative: Grounded + Structured (No Hallucinations)

We use OpenAI **Structured Outputs** so the model returns JSON matching a strict schema.

Snippet (simplified):

```py
resp = client.responses.create(
    model=m,
    instructions=instructions,
    input=user_input,
    response_format={
        "type": "json_schema",
        "json_schema": {
            "name": "locality_report_narratives",
            "schema": schema,
            "strict": True,
        },
    },
)
```

The narrative text is then attached into:

- `payload["narratives"]["pageX_..."]["..."]`

…and rendered in:
- 🧾 PDF pages
- ⚛️ UI components (via `ui/src/lib/reportData.ts`)

---

## 🧾 PDF Rendering (Tables + Narratives)

The PDF renderer prints:
- KPI tiles (asking/registration/rating/reviews)
- Chart image boxes (PNG)
- Real tables for Top Projects
- Reviews distribution + good/bad tags + review snippets
- Narratives pulled from `payload["narratives"]`

---

## 🖥️ Frontend (Lovable UI)

`ui/src/lib/reportData.ts` imports the payload and exports typed getters.  
Narratives are HTML and are rendered section-wise (Option A: one narrative block per section).

Example:

```ts
import reportPayload from "@/data/report_payload.json";

export const narratives = (reportPayload as any).narratives || {};
```

---

## 📥 Download PDF CTA

The UI includes a **Download PDF** CTA to download a PDF version of the report.

Recommended approach for **single extremely tall (one-page) PDF**:
- server-side rendering using **Playwright/Puppeteer**
- custom page height based on rendered DOM height

(Kept as the next step if required.)

---

## 🔐 Environment Variables

Create `.env` (don’t commit secrets):

```bash
OPENAI_API_KEY=...
OPENAI_MODEL=gpt-4.1-mini
```

---

## ✅ Supports Any Locality

To generate a report for another locality:
1. Drop the new JSONs into `data/`
2. Update the polygon/map asset URL or local image
3. Re-run Steps 1 → 3 → 5 → UI

No code changes needed.

---

## 📌 Output Artifacts (What you ship)

- `out/report_payload_step5.json` ✅ (single source of truth)
- `out/<Locality> Locality Report - Final.pdf` ✅
- UI running on `localhost:8080` ✅

---

## 🙌 Credits

Built for Square Yards — Automated Locality Report Engine  
Author: Deepesh Kumar Gupta
