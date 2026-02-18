import express from "express";
import cors from "cors";
import path from "path";
import { fileURLToPath } from "url";
import { renderTallPdf } from "./renderTallPdf";

const app = express();
app.use(cors());

const PORT = Number(process.env.PDF_PORT || 8787);

// Base URL of the Vite app that Playwright will load.
// In dev: http://localhost:8080 (your current UI)
const UI_BASE_URL = process.env.UI_BASE_URL || "http://localhost:8080";

app.get("/health", (_, res) => res.json({ ok: true }));

app.get("/api/pdf", async (req, res) => {
  try {
    // Optional: allow passing locality for file naming only.
    const locality = String(req.query.locality || "Locality").trim();

    const pdf = await renderTallPdf({
      uiBaseUrl: UI_BASE_URL,
    });

    const safeName = locality.replace(/[^\w\s-]/g, "").trim() || "Locality";
    const filename = `${safeName} Locality Report.pdf`;

    res.setHeader("Content-Type", "application/pdf");
    res.setHeader("Content-Disposition", `attachment; filename="${filename}"`);
    res.status(200).send(Buffer.from(pdf));
  } catch (e: any) {
    console.error("PDF render failed:", e);
    res.status(500).json({
      error: "pdf_render_failed",
      message: e?.message || String(e),
    });
  }
});

app.listen(PORT, () => {
  console.log(`PDF server listening on http://localhost:${PORT}`);
  console.log(`UI_BASE_URL = ${UI_BASE_URL}`);
});