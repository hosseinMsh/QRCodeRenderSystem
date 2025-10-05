import json
import hashlib

SHARIF_BLUE = "#1966ab"

DEFAULT_OPTIONS_JSON = {
    "type": "png",
    "width": 512,
    "height": 512,
    "margin": 10,
    "data": "https://sharif.ir",
    "qrOptions": {"errorCorrectionLevel": "Q"},
    "dotsOptions": {"type": "rounded", "color": SHARIF_BLUE},
    "backgroundOptions": {"color": "#ffffff"},
    "cornersSquareOptions": {"type": "dot", "color": SHARIF_BLUE},
    "cornersDotOptions": {"type": "dot", "color": SHARIF_BLUE},
    "image": None,
    "imageOptions": {"margin": 12, "imageSize": 0.22}
}

def build_options_from_input(data_field):
    """
    Accepts either:
      - dict (options.json-like object)
      - str (URL)
    Returns normalized options dict merged with defaults.
    """
    if isinstance(data_field, str):
        opts = dict(DEFAULT_OPTIONS_JSON)
        opts["data"] = data_field
        return opts
    if isinstance(data_field, dict):
        merged = dict(DEFAULT_OPTIONS_JSON)
        # shallow merge; for nested dicts do deeper merge if needed
        for k, v in data_field.items():
            if isinstance(v, dict) and isinstance(merged.get(k), dict):
                merged[k].update(v)
            else:
                merged[k] = v
        return merged
    # fallback
    return dict(DEFAULT_OPTIONS_JSON)

def canonical_hash(payload: dict) -> str:
    """
    Hash a request payload deterministically. We hash the payload that
    affects the image result: the 'data' object plus type/size/etc if present.
    """
    s = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(s.encode("utf-8")).hexdigest()
