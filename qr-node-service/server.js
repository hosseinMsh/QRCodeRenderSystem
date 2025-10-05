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
  type: "png", // "png" | "svg"
  data: "https://sharif.ir",
  qrOptions: { errorCorrectionLevel: "Q" },
  dotsOptions: { type: "rounded", color: "#1966ab" },
  backgroundOptions: { color: "#ffffff" },
  cornersSquareOptions: { type: "dot", color: "#1966ab" },
  cornersDotOptions: { type: "dot", color: "#1966ab" },
  image: null, // URL or data URL
  imageOptions: {
    crossOrigin: "anonymous",
    margin: 12,      // px padding around the logo
    imageSize: 0.22  // fraction of side length
  }
};

// Normalize input: accept either "data: {options.json}" or flat body
function normalizeOptions(body) {
  // If body.data is a string => treat as URL and build options
  if (typeof body?.data === "string") {
    return { ...DEFAULTS, data: body.data };
  }
  // If body.data is an object => merge with DEFAULTS
  if (body && typeof body.data === "object" && !Array.isArray(body.data)) {
    return { ...DEFAULTS, ...body.data };
  }
  // Otherwise assume body itself resembles options
  return { ...DEFAULTS, ...(body || {}) };
}

app.post("/render", async (req, res) => {
  try {
    const opts = normalizeOptions(req.body || {});
    const type = (opts.type === "svg") ? "svg" : "png";
    const qr = new QRCodeStyling(opts);

    if (type === "svg") {
      const svgBuffer = await qr.getRawData("svg");
      const asBase64 = Boolean(req.body?.asBase64 ?? true);
      if (asBase64) {
        return res.json({
          format: "svg",
          base64: "data:image/svg+xml;base64," + svgBuffer.toString("base64")
        });
      }
      res.setHeader("Content-Type", "image/svg+xml");
      if (req.body?.download) res.setHeader("Content-Disposition", 'attachment; filename="qr.svg"');
      return res.send(svgBuffer);
    }

    // PNG
    const pngBuffer = await qr.getRawData("png");
    const asBase64 = Boolean(req.body?.asBase64 ?? true);
    if (asBase64) {
      return res.json({
        format: "png",
        base64: "data:image/png;base64," + pngBuffer.toString("base64")
      });
    }
    res.setHeader("Content-Type", "image/png");
    if (req.body?.download) res.setHeader("Content-Disposition", 'attachment; filename="qr.png"');
    return res.send(pngBuffer);
  } catch (e) {
    console.error(e);
    res.status(500).json({ error: "render_failed", detail: String(e) });
  }
});

const port = process.env.PORT || 3001;
app.listen(port, () => console.log(`QR render service listening on :${port}`));
