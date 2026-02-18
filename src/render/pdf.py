from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas


PAGE_W, PAGE_H = A4
M = 36  # margin

FONT_BODY = "Helvetica"
FONT_BOLD = "Helvetica-Bold"


# -----------------------
# Safe helpers
# -----------------------
def _s(v: Any, default: str = "") -> str:
    if v is None:
        return default
    return str(v)


def _num(v: Any) -> Optional[float]:
    try:
        if v is None:
            return None
        if isinstance(v, (int, float)):
            return float(v)
        return float(str(v).replace(",", "").strip())
    except Exception:
        return None


def _pick(d: Dict[str, Any], path: str, default: Any = None) -> Any:
    cur: Any = d
    for part in path.split("."):
        if not isinstance(cur, dict):
            return default
        if part not in cur:
            return default
        cur = cur[part]
    return cur


def _strip_html_to_text(html: str) -> str:
    """
    Minimal HTML->text for PDF.
    Converts list items to bullets and strips other tags.
    """
    s = html or ""
    s = s.replace("</li>", "\n")
    s = s.replace("<li>", "- ")
    for tag in ["<ul>", "</ul>", "<ol>", "</ol>", "<p>", "</p>"]:
        s = s.replace(tag, "\n")
    for tag in ["<br>", "<br/>", "<br />"]:
        s = s.replace(tag, "\n")

    out = []
    in_tag = False
    for ch in s:
        if ch == "<":
            in_tag = True
            continue
        if ch == ">":
            in_tag = False
            continue
        if not in_tag:
            out.append(ch)

    txt = "".join(out)
    lines = [ln.strip() for ln in txt.splitlines()]
    lines = [ln for ln in lines if ln]
    return "\n".join(lines).strip()


def _wrap_lines(c: canvas.Canvas, text: str, max_w: float, font: str, size: int) -> List[str]:
    words = (text or "").split()
    if not words:
        return []
    lines: List[str] = []
    cur = words[0]
    for w in words[1:]:
        cand = cur + " " + w
        if c.stringWidth(cand, font, size) <= max_w:
            cur = cand
        else:
            lines.append(cur)
            cur = w
    lines.append(cur)
    return lines


def _get_narrative(payload: Dict[str, Any], page_key: str, key: str) -> str:
    """
    Finds narrative string in multiple supported locations.
    """
    # 0) Preferred: page-level narrative object written by Step-5
    page = payload.get(page_key) or {}
    if isinstance(page, dict):
        n0 = page.get("narrative") or {}
        if isinstance(n0, dict) and isinstance(n0.get(key), str):
            return n0[key].strip()

    n = payload.get("narratives") or {}
    if isinstance(n, dict):
        v = n.get(page_key)
        if isinstance(v, dict) and isinstance(v.get(key), str):
            return v[key].strip()
        flat = n.get(f"{page_key}.{key}")
        if isinstance(flat, str):
            return flat.strip()

    if isinstance(page, dict):
        comp = page.get("computed") or {}
        if isinstance(comp, dict):
            nn = comp.get("narratives") or comp.get("narrative") or {}
            if isinstance(nn, dict) and isinstance(nn.get(key), str):
                return nn[key].strip()
            if isinstance(comp.get(key), str):
                return comp[key].strip()

    return ""


def _get_narrative_list(payload: Dict[str, Any], page_key: str, key: str) -> List[str]:
    """Return a list narrative (bullets) from supported locations."""
    page = payload.get(page_key) or {}
    if isinstance(page, dict):
        n0 = page.get("narrative") or {}
        if isinstance(n0, dict) and isinstance(n0.get(key), list):
            return [str(x).strip() for x in n0.get(key) if str(x).strip()]

    n = payload.get("narratives") or {}
    if isinstance(n, dict):
        v = n.get(page_key)
        if isinstance(v, dict) and isinstance(v.get(key), list):
            return [str(x).strip() for x in v.get(key) if str(x).strip()]
        flat = n.get(f"{page_key}.{key}")
        if isinstance(flat, list):
            return [str(x).strip() for x in flat if str(x).strip()]

    # Back-compat: computed container
    if isinstance(page, dict):
        comp = page.get("computed") or {}
        if isinstance(comp, dict):
            nn = comp.get("narratives") or comp.get("narrative") or {}
            if isinstance(nn, dict) and isinstance(nn.get(key), list):
                return [str(x).strip() for x in nn.get(key) if str(x).strip()]
            if isinstance(comp.get(key), list):
                return [str(x).strip() for x in comp.get(key) if str(x).strip()]

    return []


# -----------------------
# Drawing primitives
# -----------------------
def _draw_header(c: canvas.Canvas, title: str, page_no: int) -> None:
    c.setFillColor(colors.black)
    c.setFont(FONT_BOLD, 12)
    c.drawString(M, PAGE_H - M + 6, title)
    c.setFont(FONT_BODY, 10)
    c.drawRightString(PAGE_W - M, PAGE_H - M + 6, f"Page {page_no}")


def _draw_footer(c: canvas.Canvas, text: str) -> None:
    c.setFillColor(colors.black)
    c.setFont(FONT_BODY, 8)
    c.drawString(M, M - 18, text)


def _draw_kpi_tile(c: canvas.Canvas, x: float, y: float, w: float, h: float, label: str, value: str) -> None:
    c.setStrokeColor(colors.HexColor("#D9DDE3"))
    c.setFillColor(colors.white)
    c.roundRect(x, y, w, h, 10, stroke=1, fill=1)

    c.setFillColor(colors.HexColor("#111827"))
    c.setFont(FONT_BODY, 9)
    c.drawString(x + 12, y + h - 18, label)

    c.setFont(FONT_BOLD, 16)
    c.drawString(x + 12, y + 16, value)


def _draw_paragraph(
    c: canvas.Canvas,
    x: float,
    y: float,
    w: float,
    text: str,
    font_size: int = 10,
    leading: int = 14,
    max_lines: Optional[int] = None,
) -> float:
    c.setFillColor(colors.HexColor("#111827"))
    c.setFont(FONT_BODY, font_size)
    lines = _wrap_lines(c, text or "", w, FONT_BODY, font_size)
    if max_lines is not None:
        lines = lines[:max_lines]
    cur_y = y
    for ln in lines:
        c.drawString(x, cur_y, ln)
        cur_y -= leading
    return cur_y


def _draw_bullets(
    c: canvas.Canvas,
    x: float,
    y: float,
    w: float,
    items: Sequence[str],
    font_size: int = 10,
    leading: int = 14,
    max_items: Optional[int] = None,
) -> float:
    cur_y = y
    take = list(items)
    if max_items is not None:
        take = take[:max_items]
    for it in take:
        it = (it or "").strip()
        if not it:
            continue
        wrapped = _wrap_lines(c, f"• {it}", w, FONT_BODY, font_size)
        for ln in wrapped:
            c.setFont(FONT_BODY, font_size)
            c.setFillColor(colors.HexColor("#111827"))
            c.drawString(x, cur_y, ln)
            cur_y -= leading
    return cur_y


def _draw_image_box(c: canvas.Canvas, x: float, y: float, w: float, h: float, img_path: Optional[str]) -> None:
    c.setStrokeColor(colors.HexColor("#D9DDE3"))
    c.setFillColor(colors.white)
    c.roundRect(x, y, w, h, 10, stroke=1, fill=1)

    if not img_path:
        c.setFillColor(colors.HexColor("#6B7280"))
        c.setFont(FONT_BODY, 9)
        c.drawString(x + 12, y + h / 2, "Chart not available")
        return

    p = Path(img_path)
    if not p.exists():
        c.setFillColor(colors.HexColor("#6B7280"))
        c.setFont(FONT_BODY, 9)
        c.drawString(x + 12, y + h / 2, "Chart file missing")
        return

    img = ImageReader(str(p))
    c.drawImage(img, x + 10, y + 10, w - 20, h - 20, preserveAspectRatio=True, anchor="c")


# -----------------------
# Table renderer
# -----------------------
@dataclass
class TableSpec:
    headers: List[str]
    col_widths: List[float]
    row_h: float = 18
    font_size: int = 9
    header_fill: colors.Color = colors.HexColor("#F2F3F5")
    row_alt_fill: colors.Color = colors.HexColor("#FBFCFD")
    grid: colors.Color = colors.HexColor("#D9DDE3")


def _draw_table(
    c: canvas.Canvas,
    x: float,
    y_top: float,
    w: float,
    rows: Sequence[Sequence[str]],
    spec: TableSpec,
    max_rows: Optional[int] = None,
) -> float:
    """
    Draw table from y_top downward. Returns y_bottom.
    """
    col_w = spec.col_widths
    if sum(col_w) > w + 1e-6:
        raise ValueError("col_widths exceed table width")

    # header
    c.setFillColor(spec.header_fill)
    c.rect(x, y_top - spec.row_h, w, spec.row_h, fill=1, stroke=0)

    c.setFillColor(colors.HexColor("#111827"))
    c.setFont(FONT_BOLD, spec.font_size)
    cx = x
    for i, h in enumerate(spec.headers):
        c.drawString(cx + 6, y_top - spec.row_h + 6, _s(h)[:60])
        cx += col_w[i]

    c.setStrokeColor(spec.grid)
    c.line(x, y_top - spec.row_h, x + w, y_top - spec.row_h)

    cur_y = y_top - spec.row_h
    take = list(rows)
    if max_rows is not None:
        take = take[:max_rows]

    for r_i, row in enumerate(take):
        cur_y -= spec.row_h
        fill = colors.white if r_i % 2 == 0 else spec.row_alt_fill
        c.setFillColor(fill)
        c.rect(x, cur_y, w, spec.row_h, fill=1, stroke=0)

        c.setFillColor(colors.HexColor("#111827"))
        c.setFont(FONT_BODY, spec.font_size)
        cx = x
        for i, cell in enumerate(row):
            txt = _s(cell)
            # truncate
            max_chars = 36 if col_w[i] < 140 else 60
            if len(txt) > max_chars:
                txt = txt[: max_chars - 1] + "…"
            c.drawString(cx + 6, cur_y + 6, txt)
            cx += col_w[i]

        c.setStrokeColor(spec.grid)
        c.line(x, cur_y, x + w, cur_y)

    # vertical grid
    cx = x
    c.setStrokeColor(spec.grid)
    c.line(x, y_top, x, cur_y)
    for cw in col_w:
        cx += cw
        c.line(cx, y_top, cx, cur_y)

    return cur_y


# -----------------------
# Main render
# -----------------------
def render_pdf(payload: Dict[str, Any], out_pdf: Path) -> None:
    c = canvas.Canvas(str(out_pdf), pagesize=A4)

    p1 = payload.get("page1_cover")
    if p1:
        _render_page1_cover(c, payload, p1)

    for page_no, key, fn in [
        (2, "page2_exec_snapshot", _render_page2_exec),
        (3, "page3_liveability", _render_page3_liveability),
        (4, "page4_market_snapshot", _render_page4_market),
        (5, "page5_price_trend", _render_page5_trend),
        (6, "page6_nearby_comparison", _render_page6_nearby),
        (7, "page7_demand_supply_sale", lambda cc, pp, px, pn: _render_page7_ds(cc, pp, px, pn, "sale")),
        (8, "page8_demand_supply_rent", lambda cc, pp, px, pn: _render_page7_ds(cc, pp, px, pn, "rent")),
        (9, "page9_propertytype_status", _render_page9_type_status),
        (10, "page10_top_projects", _render_page10_projects),
        (11, "page11_registrations_developers", _render_page11_regs_devs),
        (12, "page12_reviews_conclusion", _render_page12_reviews),
    ]:
        px = payload.get(key)
        if px:
            c.showPage()
            fn(c, payload, px, page_no)

    c.save()


# -----------------------
# Pages
# -----------------------
def _render_page1_cover(c: canvas.Canvas, payload: Dict[str, Any], p1: Dict[str, Any]) -> None:
    d = p1.get("data", {}) or {}
    title = d.get("title", "Locality Report")
    city = d.get("city", "")
    mm = d.get("micromarket", "")
    period = (p1.get("computed", {}) or {}).get("report_period_label", "")

    c.setFillColor(colors.HexColor("#F2F3F5"))
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)

    c.setFillColor(colors.HexColor("#111827"))
    c.setFont(FONT_BOLD, 28)
    c.drawString(M, PAGE_H - 120, title)

    c.setFont(FONT_BODY, 14)
    c.drawString(M, PAGE_H - 150, f"{city} | {mm}")

    if period:
        c.setFont(FONT_BODY, 12)
        c.drawString(M, PAGE_H - 175, period)

    polygon_local = (payload.get("assets", {}) or {}).get("polygon_thumbnail_local")
    c.setFont(FONT_BOLD, 12)
    c.drawString(M, PAGE_H - 230, "Locality Map")
    _draw_image_box(c, M, 140, PAGE_W - 2 * M, PAGE_H - 400, polygon_local)

    _draw_footer(c, "Generated by Square Yards - Automated Locality Report Engine")


def _render_page2_exec(c: canvas.Canvas, payload: Dict[str, Any], p2: Dict[str, Any], page_no: int) -> None:
    _draw_header(c, "Executive Summary Snapshot", page_no)
    d = p2.get("data", {}) or {}

    mo = d.get("marketOverview", {}) or {}
    asking = mo.get("askingPrice")
    reg = mo.get("registrationRate")

    rr = d.get("ratingReviewData", {}) or {}
    avg = rr.get("AvgRating")
    rc = rr.get("ReviewCount")

    x0 = M
    y0 = PAGE_H - M - 120
    tile_w = (PAGE_W - 2 * M - 20) / 2
    tile_h = 70

    _draw_kpi_tile(c, x0, y0, tile_w, tile_h, "Buy - Asking Price (₹/sq ft)", _s(asking, "NA"))
    _draw_kpi_tile(c, x0 + tile_w + 20, y0, tile_w, tile_h, "Buy - Registration Rate (₹/sq ft)", _s(reg, "NA"))

    y1 = y0 - 90
    _draw_kpi_tile(c, x0, y1, tile_w, tile_h, "Locality Rating (Avg)", _s(avg, "NA"))
    _draw_kpi_tile(c, x0 + tile_w + 20, y1, tile_w, tile_h, "Reviews Count", _s(rc, "NA"))

    charts = (payload.get("charts", {}) or {})
    spark = charts.get("p5_price_trend")
    c.setFont(FONT_BOLD, 12)
    c.setFillColor(colors.HexColor("#111827"))
    c.drawString(M, y1 - 40, "Recent Price Movement (last 4 quarters)")
    _draw_image_box(c, M, 270, PAGE_W - 2 * M, 150, spark)

    # LLM narratives (Step-5) can be either a bullet list or HTML/text.
    takeaways_list = _get_narrative_list(payload, "page2_exec_snapshot", "key_takeaways")
    takeaways_html = _get_narrative(payload, "page2_exec_snapshot", "takeaways")
    c.setFont(FONT_BOLD, 12)
    c.drawString(M, 240, "Key Takeaways")
    if takeaways_list:
        _draw_bullets(c, M, 220, PAGE_W - 2 * M, takeaways_list, font_size=10, leading=14, max_items=5)
    elif takeaways_html:
        txt = _strip_html_to_text(takeaways_html)
        items = [ln[2:].strip() for ln in txt.splitlines() if ln.startswith("- ")]
        if items:
            _draw_bullets(c, M, 220, PAGE_W - 2 * M, items, font_size=10, leading=14, max_items=5)
        else:
            _draw_paragraph(c, M, 220, PAGE_W - 2 * M, txt, 10, 14, max_lines=8)
    else:
        _draw_paragraph(c, M, 220, PAGE_W - 2 * M, "Key takeaways are not available for this report.", 10, 14)

    _draw_footer(c, "Note: Demand% is a behavioral signal, not confirmed market demand.")


def _render_page3_liveability(c: canvas.Canvas, payload: Dict[str, Any], p3: Dict[str, Any], page_no: int) -> None:
    _draw_header(c, "Locality Profile & Liveability Indices", page_no)
    d = p3.get("data", {}) or {}

    loc = d.get("localityOverviewData", {}) or {}
    indices = d.get("indices", {}) or {}

    c.setFont(FONT_BODY, 11)
    c.setFillColor(colors.HexColor("#111827"))
    loc_name = loc.get("name") or "NA"
    city = loc.get("cityName") or loc.get("city") or "NA"
    micro = loc.get("dotcomLocationName") or loc.get("micromarket") or "NA"
    c.drawString(M, PAGE_H - M - 40, f"Locality: {loc_name} | City: {city} | Micro-market: {micro}")

    cards = [
        ("Connectivity", indices.get("connectivity_index")),
        ("Lifestyle", indices.get("lifestyle_index")),
        ("Education & Health", indices.get("educationhealth_index")),
        ("Livability", indices.get("livability_index")),
    ]

    x = M
    y = PAGE_H - M - 120
    cw = (PAGE_W - 2 * M - 20) / 2
    ch = 90

    for i, (label, score) in enumerate(cards):
        cx = x + (i % 2) * (cw + 20)
        cy = y - (i // 2) * (ch + 20)
        c.setStrokeColor(colors.HexColor("#D9DDE3"))
        c.setFillColor(colors.white)
        c.roundRect(cx, cy, cw, ch, 10, stroke=1, fill=1)

        c.setFillColor(colors.HexColor("#111827"))
        c.setFont(FONT_BOLD, 12)
        c.drawString(cx + 12, cy + ch - 22, label)
        c.setFont(FONT_BOLD, 24)
        c.drawString(cx + 12, cy + 22, f"{score if score is not None else 'NA'} / 5")

    live = _get_narrative(payload, "page3_liveability", "liveability_summary") or _get_narrative(
        payload, "page3_liveability", "summary"
    )
    c.setFont(FONT_BOLD, 12)
    c.drawString(M, 330, "What living here feels like")
    if live:
        _draw_paragraph(c, M, 310, PAGE_W - 2 * M, _strip_html_to_text(live), 10, 14, max_lines=9)
    else:
        _draw_paragraph(c, M, 310, PAGE_W - 2 * M, "Liveability narrative is not available for this report.", 10, 14)

    _draw_footer(c, "Indices are computed from nearby POIs and connectivity signals.")


def _render_page4_market(c: canvas.Canvas, payload: Dict[str, Any], p4: Dict[str, Any], page_no: int) -> None:
    _draw_header(c, "Market Snapshot (Buy + Rent)", page_no)
    charts = (payload.get("charts", {}) or {})
    hist = charts.get("p4_supply_hist")
    rent = charts.get("p4_rent_bhk")

    c.setFont(FONT_BOLD, 12)
    c.setFillColor(colors.HexColor("#111827"))
    c.drawString(M, PAGE_H - M - 50, "Buy: Market Supply Distribution")
    _draw_image_box(c, M, PAGE_H - 420, PAGE_W - 2 * M, 320, hist)

    c.setFont(FONT_BOLD, 12)
    c.drawString(M, 320, "Rent: Avg Monthly Rent by Unit Type")
    _draw_image_box(c, M, 70, PAGE_W - 2 * M, 230, rent)

    _draw_footer(c, "Market supply reflects marketplace listings; registrations reflect government records for the stated period.")


def _render_page5_trend(c: canvas.Canvas, payload: Dict[str, Any], p5: Dict[str, Any], page_no: int) -> None:
    _draw_header(c, "Asking Price Trend (Locality vs Micro-market)", page_no)
    charts = (payload.get("charts", {}) or {})
    trend = charts.get("p5_price_trend")

    _draw_image_box(c, M, 300, PAGE_W - 2 * M, 380, trend)

    narrative = _get_narrative(payload, "page5_price_trend", "trend_narrative") or _get_narrative(
        payload, "page5_price_trend", "narrative"
    )
    bullets = _get_narrative_list(payload, "page5_price_trend", "bullets")
    c.setFont(FONT_BOLD, 12)
    c.setFillColor(colors.HexColor("#111827"))
    c.drawString(M, 270, "Trend Narrative")
    if narrative:
        y = _draw_paragraph(c, M, 250, PAGE_W - 2 * M, _strip_html_to_text(narrative), 10, 14, max_lines=6)
        if bullets:
            _draw_bullets(c, M, y - 4, PAGE_W - 2 * M, bullets, font_size=10, leading=14, max_items=3)
    else:
        if bullets:
            _draw_bullets(c, M, 250, PAGE_W - 2 * M, bullets, font_size=10, leading=14, max_items=4)
        else:
            _draw_paragraph(c, M, 250, PAGE_W - 2 * M, "Trend narrative is not available for this report.", 10, 14)

    _draw_footer(c, "Trend series is limited to available quarters in the source feed.")


def _render_page6_nearby(c: canvas.Canvas, payload: Dict[str, Any], p6: Dict[str, Any], page_no: int) -> None:
    _draw_header(c, "Locality vs Nearby Localities", page_no)
    charts = (payload.get("charts", {}) or {})
    nearby = charts.get("p6_nearby_bar")

    _draw_image_box(c, M, 300, PAGE_W - 2 * M, 380, nearby)

    narrative = _get_narrative(payload, "page6_nearby_comparison", "nearby_narrative") or _get_narrative(
        payload, "page6_nearby_comparison", "narrative"
    )
    bullets = _get_narrative_list(payload, "page6_nearby_comparison", "bullets")
    c.setFont(FONT_BOLD, 12)
    c.setFillColor(colors.HexColor("#111827"))
    c.drawString(M, 270, "Interpretation")
    if narrative:
        y = _draw_paragraph(c, M, 250, PAGE_W - 2 * M, _strip_html_to_text(narrative), 10, 14, max_lines=6)
        if bullets:
            _draw_bullets(c, M, y - 4, PAGE_W - 2 * M, bullets, font_size=10, leading=14, max_items=3)
    else:
        if bullets:
            _draw_bullets(c, M, 250, PAGE_W - 2 * M, bullets, font_size=10, leading=14, max_items=4)
        else:
            _draw_paragraph(c, M, 250, PAGE_W - 2 * M, "Nearby comparison narrative is not available for this report.", 10, 14)

    _draw_footer(c, "Nearby set is sourced from DI locationRates in JSON-2.")


def _render_page7_ds(c: canvas.Canvas, payload: Dict[str, Any], pX: Dict[str, Any], page_no: int, mode: str) -> None:
    title = f"Demand vs Supply ({'Buy' if mode == 'sale' else 'Rent'}) Segmentation"
    _draw_header(c, title, page_no)

    charts = (payload.get("charts", {}) or {})
    unit = charts.get(f"p{page_no}_ds_unit")
    ptype = charts.get(f"p{page_no}_ds_ptype")
    band = charts.get(f"p{page_no}_ds_band")

    c.setFont(FONT_BOLD, 11)
    c.setFillColor(colors.HexColor("#111827"))
    c.drawString(M, PAGE_H - M - 50, "By Unit Type")
    _draw_image_box(c, M, PAGE_H - 300, PAGE_W - 2 * M, 220, unit)

    c.setFont(FONT_BOLD, 11)
    c.drawString(M, PAGE_H - 330, "By Property Type")
    _draw_image_box(c, M, PAGE_H - 580, PAGE_W - 2 * M, 220, ptype)

    c.setFont(FONT_BOLD, 11)
    c.drawString(M, 230, "By Price Band")
    _draw_image_box(c, M, 40, PAGE_W - 2 * M, 180, band)

    _draw_footer(c, "Gap = demand% - supply%. Demand% is a signal derived from user behavior/enquiries.")


def _render_page9_type_status(c: canvas.Canvas, payload: Dict[str, Any], p9: Dict[str, Any], page_no: int) -> None:
    _draw_header(c, "Rates by Property Type and Project Status", page_no)
    charts = (payload.get("charts", {}) or {})
    pt = charts.get("p9_property_types")
    st = charts.get("p9_property_status")

    c.setFont(FONT_BOLD, 12)
    c.setFillColor(colors.HexColor("#111827"))
    c.drawString(M, PAGE_H - M - 50, "Rates by Property Type")
    _draw_image_box(c, M, PAGE_H - 380, PAGE_W - 2 * M, 300, pt)

    c.setFont(FONT_BOLD, 12)
    c.drawString(M, 320, "Rates by Project Status")
    _draw_image_box(c, M, 70, PAGE_W - 2 * M, 230, st)

    _draw_footer(c, "Change% is derived from the source feed and reflects the stated comparison window.")


def _render_page10_projects(c: canvas.Canvas, payload: Dict[str, Any], p10: Dict[str, Any], page_no: int) -> None:
    _draw_header(c, "Top Projects (Transactions · Rates · Value)", page_no)

    tp = _pick(p10, "data.topProjects", {}) or {}
    by_txn = _pick(tp, "byTransactions.projects", []) or []
    by_rate = _pick(tp, "byListingRates.projects", []) or []
    by_val = _pick(tp, "byValue.projects", []) or []

    # LLM highlights are expected as a list in Step-5 schema.
    highlights_list = _get_narrative_list(payload, "page10_top_projects", "highlights")
    highlights_text = _get_narrative(payload, "page10_top_projects", "highlights")
    c.setFont(FONT_BOLD, 11)
    c.setFillColor(colors.HexColor("#111827"))
    c.drawString(M, PAGE_H - M - 45, "Highlights")
    if highlights_list:
        _draw_bullets(c, M, PAGE_H - M - 62, PAGE_W - 2 * M, highlights_list, font_size=9, leading=12, max_items=3)
    elif highlights_text:
        _draw_paragraph(c, M, PAGE_H - M - 62, PAGE_W - 2 * M, _strip_html_to_text(highlights_text), 9, 12, max_lines=3)
    else:
        _draw_paragraph(c, M, PAGE_H - M - 62, PAGE_W - 2 * M, "Highlights are not available for this report.", 9, 12, max_lines=3)

    table_w = PAGE_W - 2 * M
    spec = TableSpec(
        headers=["#", "Project", "Locality", "Metric", "Rate", "Δ%"],
        col_widths=[24, 220, 130, 60, 70, table_w - (24 + 220 + 130 + 60 + 70)],
        row_h=18,
        font_size=8,
    )

    def rows_for(arr: List[Dict[str, Any]], metric_key: str) -> List[List[str]]:
        out: List[List[str]] = []
        for i, p in enumerate(arr[:10]):
            rate = p.get("currentRate")
            ch = p.get("changePercentage")
            out.append(
                [
                    str(i + 1),
                    _s(p.get("projectName")),
                    _s(p.get("locality")),
                    _s(p.get(metric_key), "—"),
                    f"₹ {int(rate):,}" if isinstance(rate, (int, float)) else _s(rate, "—"),
                    f"{float(ch):+.1f}%" if isinstance(ch, (int, float)) else "—",
                ]
            )
        return out

    y = PAGE_H - M - 110

    c.setFont(FONT_BOLD, 11)
    c.drawString(M, y, "Top by Transactions")
    y = _draw_table(c, M, y - 8, table_w, rows_for(by_txn, "noOfTransactions"), spec, max_rows=10)

    y -= 24
    c.setFont(FONT_BOLD, 11)
    c.drawString(M, y, "Top by Listing Rate")
    y = _draw_table(c, M, y - 8, table_w, rows_for(by_rate, "currentRate"), spec, max_rows=10)

    y -= 24
    c.setFont(FONT_BOLD, 11)
    c.drawString(M, y, "Top by Gross Value")
    if by_val:
        y = _draw_table(c, M, y - 8, table_w, rows_for(by_val, "grossValue"), spec, max_rows=10)
    else:
        c.setFont(FONT_BODY, 9)
        c.setFillColor(colors.HexColor("#6B7280"))
        c.drawString(M, y - 16, "Data not available in current source feed (topProjects.byValue).")

    _draw_footer(c, "Leaderboards are computed from available source fields; missing values are shown as —.")


def _render_page11_regs_devs(c: canvas.Canvas, payload: Dict[str, Any], p11: Dict[str, Any], page_no: int) -> None:
    _draw_header(c, "Registration Overview + Top Developers", page_no)
    charts = (payload.get("charts", {}) or {})
    dev_txn = charts.get("p11_devs_txn")

    d = p11.get("data", {}) or {}
    g1 = d.get("govtRegistration_json1", {}) or {}

    txn = g1.get("transactionCount")
    gross = g1.get("grossValue")
    dr = g1.get("dateRange")
    rr = g1.get("registeredRate")

    c.setFont(FONT_BOLD, 12)
    c.setFillColor(colors.HexColor("#111827"))
    c.drawString(M, PAGE_H - M - 50, "Govt Registration Summary (JSON-1)")
    _draw_paragraph(
        c,
        M,
        PAGE_H - M - 70,
        PAGE_W - 2 * M,
        f"Transactions: {txn} | Gross Value: {gross} | Period: {dr} | Avg Registered Rate: {rr}",
        10,
        14,
        max_lines=2,
    )

    c.setFont(FONT_BOLD, 12)
    c.drawString(M, PAGE_H - 160, "Top Developers by Transactions")
    _draw_image_box(c, M, 300, PAGE_W - 2 * M, 280, dev_txn)

    bullets = _get_narrative_list(payload, "page11_registrations_developers", "bullets")
    narrative = _get_narrative(payload, "page11_registrations_developers", "narrative")
    c.setFont(FONT_BOLD, 12)
    c.drawString(M, 270, "Interpretation")
    if bullets:
        _draw_bullets(c, M, 252, PAGE_W - 2 * M, bullets, font_size=10, leading=14, max_items=5)
    elif narrative:
        _draw_paragraph(c, M, 252, PAGE_W - 2 * M, _strip_html_to_text(narrative), 10, 14, max_lines=6)
    else:
        _draw_paragraph(c, M, 252, PAGE_W - 2 * M, "Interpretation narrative is not available for this report.", 10, 14, max_lines=6)

    _draw_footer(c, "Registrations are government-recorded; marketplace listings are separate supply signals.")


def _render_page12_reviews(c: canvas.Canvas, payload: Dict[str, Any], p12: Dict[str, Any], page_no: int) -> None:
    _draw_header(c, "Ratings & Reviews + Conclusion", page_no)

    d = p12.get("data", {}) or {}
    rrd = d.get("ratingReviewData", {}) or {}
    rr = d.get("ratingReview", {}) or {}

    avg = rrd.get("AvgRating")
    reviews = rrd.get("ReviewCount")

    star_counts = rr.get("ratingStarCount") or []
    good = rr.get("good") or []
    bad = rr.get("bad") or []
    top_reviews = rr.get("topReviews") or []

    # KPIs
    x0 = M
    y0 = PAGE_H - M - 110
    tile_w = (PAGE_W - 2 * M - 20) / 2
    tile_h = 60
    _draw_kpi_tile(c, x0, y0, tile_w, tile_h, "Avg Rating", f"{avg if avg is not None else 'NA'} / 5")
    _draw_kpi_tile(c, x0 + tile_w + 20, y0, tile_w, tile_h, "Reviews Count", _s(reviews, "NA"))

    # Star distribution bars
    c.setFont(FONT_BOLD, 11)
    c.setFillColor(colors.HexColor("#111827"))
    c.drawString(M, y0 - 30, "Star Distribution")

    total = 0
    for sc in star_counts:
        total += int(_num(sc.get("Count")) or 0)

    bar_x = M
    cur_y = y0 - 50
    bar_w = PAGE_W - 2 * M
    bar_h = 10

    for sc in sorted(star_counts, key=lambda x: int(_num(x.get("Rating")) or 0), reverse=True):
        rating = int(_num(sc.get("Rating")) or 0)
        cnt = int(_num(sc.get("Count")) or 0)
        pct = (cnt / total) if total > 0 else 0.0

        c.setFont(FONT_BODY, 9)
        c.setFillColor(colors.HexColor("#111827"))
        c.drawString(bar_x, cur_y, f"{rating}★")

        c.setFillColor(colors.HexColor("#E9EDF2"))
        c.rect(bar_x + 22, cur_y - 3, bar_w - 90, bar_h, fill=1, stroke=0)

        c.setFillColor(colors.HexColor("#C9A227"))
        c.rect(bar_x + 22, cur_y - 3, (bar_w - 90) * pct, bar_h, fill=1, stroke=0)

        c.setFillColor(colors.HexColor("#6B7280"))
        c.drawRightString(bar_x + bar_w, cur_y, f"{cnt}")
        cur_y -= 16

    # Good / bad tags (bullets)
    c.setFillColor(colors.HexColor("#111827"))
    c.setFont(FONT_BOLD, 11)
    c.drawString(M, 420, "What residents like")
    likes = [f"{g.get('Name','')} ({float(_num(g.get('Percentage')) or 0):.0f}%)" for g in good[:6]]
    _draw_bullets(c, M, 402, PAGE_W - 2 * M, likes, font_size=9, leading=12, max_items=6)

    c.setFont(FONT_BOLD, 11)
    c.drawString(M, 330, "Areas for improvement")
    dislikes = [f"{b.get('Name','')} ({float(_num(b.get('Percentage')) or 0):.0f}%)" for b in bad[:6]]
    _draw_bullets(c, M, 312, PAGE_W - 2 * M, dislikes, font_size=9, leading=12, max_items=6)

    # Review snippets
    c.setFont(FONT_BOLD, 11)
    c.drawString(M, 240, "Recent Reviews (snippets)")
    y = 222
    for r in top_reviews[:3]:
        name = _s(r.get("Name"), "User")
        persona = _s(_pick(r, "rating_user_persona.Name", ""), "")
        rating = r.get("Rating")

        head = f"{name} ({persona})" if persona else name
        if rating is not None:
            head = f"{head} | {rating}★"

        c.setFont(FONT_BOLD, 9)
        c.setFillColor(colors.HexColor("#111827"))
        c.drawString(M, y, head)
        y -= 12

        snippet = _s(r.get("PositiveDesc") or r.get("NegativeDesc") or "", "")
        snippet = " ".join(snippet.split())
        y = _draw_paragraph(c, M, y, PAGE_W - 2 * M, snippet, 9, 12, max_lines=3)
        y -= 10
        if y < 120:
            break

    # LLM summary/conclusion (Step-5 schema)
    strengths = _get_narrative_list(payload, "page12_reviews_conclusion", "strengths")
    challenges = _get_narrative_list(payload, "page12_reviews_conclusion", "challenges")
    opportunities = _get_narrative_list(payload, "page12_reviews_conclusion", "opportunities")
    closing_note = _get_narrative(payload, "page12_reviews_conclusion", "closing_note")

    # Conclusion narrative
    c.setFont(FONT_BOLD, 11)
    c.setFillColor(colors.HexColor("#111827"))
    c.drawString(M, 128, "Conclusion")

    y0 = 112
    # Render up to 3 mini-sections (strengths/challenges/opportunities) if present.
    if strengths:
        c.setFont(FONT_BOLD, 9)
        c.drawString(M, y0, "Strengths")
        y0 = _draw_bullets(c, M, y0 - 12, PAGE_W - 2 * M, strengths, font_size=9, leading=12, max_items=3) - 6
    if challenges:
        c.setFont(FONT_BOLD, 9)
        c.drawString(M, y0, "Challenges")
        y0 = _draw_bullets(c, M, y0 - 12, PAGE_W - 2 * M, challenges, font_size=9, leading=12, max_items=3) - 6
    if opportunities:
        c.setFont(FONT_BOLD, 9)
        c.drawString(M, y0, "Opportunities")
        y0 = _draw_bullets(c, M, y0 - 12, PAGE_W - 2 * M, opportunities, font_size=9, leading=12, max_items=3) - 6

    if closing_note:
        c.setFont(FONT_BODY, 10)
        _draw_paragraph(c, M, max(y0, 70), PAGE_W - 2 * M, _strip_html_to_text(closing_note), 10, 14, max_lines=4)
    else:
        c.setFont(FONT_BODY, 10)
        _draw_paragraph(c, M, max(y0, 70), PAGE_W - 2 * M, "Closing note is not available for this report.", 10, 14, max_lines=4)

    _draw_footer(c, "Note: Review sentiment is not inferred unless explicitly computed from source text.")