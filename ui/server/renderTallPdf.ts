import { chromium } from "playwright";

type Args = {
  uiBaseUrl: string;
};

export async function renderTallPdf({ uiBaseUrl }: Args): Promise<Uint8Array> {
  const browser = await chromium.launch({
    headless: true,
    args: [
      "--no-sandbox",
      "--disable-setuid-sandbox",
      "--font-render-hinting=medium",
    ],
  });

  const context = await browser.newContext({
    viewport: { width: 1200, height: 900 }, // desktop layout like your screenshot
    deviceScaleFactor: 1,
  });

  const page = await context.newPage();

  // Print-only view (no nav) + pdf=1 for any extra “hide” CSS if needed
  const url = `${uiBaseUrl}/?print=1&pdf=1`;

  // Load and wait
  await page.goto(url, { waitUntil: "networkidle" });

  // Give charts time to render (Recharts/SVG sometimes needs a beat)
  await page.waitForTimeout(1200);

  // Measure full document size
  const dims = await page.evaluate(() => {
    const el = document.documentElement;
    const body = document.body;

    const width = Math.max(
      el.scrollWidth,
      el.offsetWidth,
      body ? body.scrollWidth : 0,
      body ? body.offsetWidth : 0
    );

    const height = Math.max(
      el.scrollHeight,
      el.offsetHeight,
      body ? body.scrollHeight : 0,
      body ? body.offsetHeight : 0
    );

    return { width, height };
  });

  // IMPORTANT: Chromium has practical limits for page height.
  // If height becomes too large, PDF generation may fail.
  // We keep a safe cap; if exceeded, we fall back to multi-page A4.
  const MAX_TALL_PX = 45000;

  let pdf: Uint8Array;

  if (dims.height <= MAX_TALL_PX) {
    pdf = await page.pdf({
      printBackground: true,
      preferCSSPageSize: false,
      margin: { top: "0px", right: "0px", bottom: "0px", left: "0px" },
      width: `${Math.max(dims.width, 1200)}px`,
      height: `${dims.height}px`,
      pageRanges: "1",
    });
  } else {
    // Fallback: multi-page A4 if the report is too tall for single-page PDF
    pdf = await page.pdf({
      printBackground: true,
      format: "A4",
      margin: { top: "8mm", right: "8mm", bottom: "8mm", left: "8mm" },
    });
  }

  await context.close();
  await browser.close();

  return pdf;
}