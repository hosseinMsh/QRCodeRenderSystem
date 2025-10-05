// server.js
const express = require("express");
const bodyParser = require("body-parser");
const { QRCodeCanvas } = require("@loskir/styled-qr-code-node");

const app = express();
app.use(bodyParser.json({ limit: "20mb" }));

// Server-side defaults (Sharif blue on white)
const DEFAULTS = {
  width: 512,
  height: 512,
  margin: 10,
  type: "png", // "png" | "svg" | "jpg" | "jpeg" | "pdf"
  data: "https://sharif.ir",
  qrOptions: { errorCorrectionLevel: "Q" },
  dotsOptions: { type: "rounded", color: "#1966ab" },
  backgroundOptions: { color: "#ffffff" },
  cornersSquareOptions: { type: "dot", color: "#1966ab" },
  cornersDotOptions: { type: "dot", color: "#1966ab" },
  image: null, // URL or data URL (data:image/...;base64,...)
  imageOptions: { margin: 12, imageSize: 0.22 }
};

function isValidImageRef(v) {
  if (!v || typeof v !== "string") return false;
  if (v.startsWith("data:image/") && v.includes(";base64,")) return true;
  if (v.startsWith("http://") || v.startsWith("https://")) return true;
  return false;
}

// Normalize input: accept either "data: {options.json}" or string URL or flat body
function normalizeOptions(body) {
  let opts;
  if (typeof body?.data === "string") {
    opts = { ...DEFAULTS, data: body.data };
  } else if (body && typeof body.data === "object" && !Array.isArray(body.data)) {
    // shallow + one-level deep merge
    opts = { ...DEFAULTS };
    for (const [k, v] of Object.entries(body.data)) {
      if (typeof v === "object" && !Array.isArray(v) && typeof opts[k] === "object") {
        opts[k] = { ...opts[k], ...v };
      } else {
        opts[k] = v;
      }
    }
  } else {
    opts = { ...DEFAULTS, ...(body || {}) };
  }

  // If image is invalid/empty, remove it entirely to avoid "Missing Source URL"
  if (!isValidImageRef(opts.image)) delete opts.image;

  // Normalize type
  const t = (opts.type || "png").toLowerCase();
  opts.type = ["svg", "pdf", "jpg", "jpeg"].includes(t) ? t : "png";

  return opts;
}

app.post("/render", async (req, res) => {
  try {
    const opts = normalizeOptions(req.body || {});
    const format = opts.type; // already normalized
    const asBase64 = Boolean(req.body?.asBase64 ?? true);
    const download = Boolean(req.body?.download ?? false);

    const qr = new QRCodeCanvas(opts);

    if (asBase64) {
      const dataUrl = await qr.toDataUrl(format); // "data:image/...;base64,...."
      return res.json({ format: format === "jpeg" ? "jpg" : format, base64: dataUrl });
    }

    const buffer = await qr.toBuffer(format);
    const contentType =
      format === "svg" ? "image/svg+xml" :
      format === "pdf" ? "application/pdf" :
      (format === "jpg" || format === "jpeg") ? "image/jpeg" :
      "image/png";

    res.setHeader("Content-Type", contentType);
    if (download) {
      const ext = format === "jpeg" ? "jpg" : format;
      res.setHeader("Content-Disposition", `attachment; filename="qr.${ext}"`);
    }
    return res.send(buffer);
  } catch (e) {
    console.error(e);
    res.status(500).json({ error: "render_failed", detail: String(e) });
  }
});

const port = process.env.PORT || 3001;
app.listen(port, () => console.log(`QR render service listening on :${port}`));
