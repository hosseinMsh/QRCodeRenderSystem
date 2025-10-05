import json
import requests
from django.http import JsonResponse, HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings
from .models import QRRender
from .utils import build_options_from_input, canonical_hash

# Node render endpoint
QR_NODE_URL = getattr(settings, "QR_NODE_URL", "http://localhost:3001/render")

@csrf_exempt
@require_POST
def generate_qr(request):
    """
    POST body:
    {
      "data": { /* options.json */ } | "https://example.com",
      "asBase64": true/false,
      "download": true/false
    }
    Behavior:
      - Normalize 'data' into options.json (with defaults if 'data' is URL).
      - Compute hash; if exists in DB -> return cached.
      - Else call Node service with:
           { data: <options.json>, asBase64: true/false, download: true/false }
        Store base64 in DB and return according to asBase64/download.
    """
    try:
        body = json.loads(request.body.decode("utf-8"))
    except Exception:
        return HttpResponseBadRequest("Invalid JSON")

    data_field = body.get("data")
    if data_field is None:
        return HttpResponseBadRequest("Field 'data' is required")

    as_base64 = bool(body.get("asBase64", True))
    download = bool(body.get("download", False))

    # Build normalized options.json (with defaults if 'data' is URL)
    options = build_options_from_input(data_field)

    # For caching, build a "signature payload" that affects image result.
    # Here we use the exact options object (since we pass it to Node).
    signature_payload = options
    sig = canonical_hash(signature_payload)

    # Try to return from DB cache
    cached = QRRender.objects.filter(options_hash=sig).first()
    if cached:
        if as_base64:
            return JsonResponse({"format": cached.fmt, "base64": cached.image_base64})
        # return binary stream
        # Decode base64 data URL
        try:
            header, b64data = cached.image_base64.split(",", 1)
        except ValueError:
            return JsonResponse({"error": "cached_data_invalid"}, status=500)
        import base64
        raw = base64.b64decode(b64data)
        content_type = "image/svg+xml" if cached.fmt == "svg" else "image/png"
        resp = HttpResponse(raw, content_type=content_type)
        if download:
            fname = f"qr.{ 'svg' if cached.fmt=='svg' else 'png' }"
            resp["Content-Disposition"] = f'attachment; filename="{fname}"'
        return resp

    # Not in cache → request Node service
    try:
        node_payload = {
            "data": options,       # send options.json in `data`
            "asBase64": True,      # always ask Node to return base64 for storage
            "download": False
        }
        r = requests.post(QR_NODE_URL, json=node_payload, timeout=30)
        if r.status_code >= 400:
            return JsonResponse({"error": "node_failed", "detail": r.text}, status=502)
        out = r.json()
        fmt = out.get("format", "png")
        base64_dataurl = out.get("base64")
        if not base64_dataurl:
            return JsonResponse({"error": "node_no_base64"}, status=502)
    except Exception as e:
        return JsonResponse({"error": "node_exception", "detail": str(e)}, status=502)

    # Store in DB (always as base64)
    obj = QRRender.objects.create(
        options_hash=sig,
        options_json=options,
        fmt=fmt,
        image_base64=base64_dataurl
    )

    # Return based on requested style
    if as_base64:
        return JsonResponse({"format": obj.fmt, "base64": obj.image_base64})

    # Binary stream response
    try:
        header, b64data = obj.image_base64.split(",", 1)
    except ValueError:
        return JsonResponse({"error": "stored_data_invalid"}, status=500)

    import base64
    raw = base64.b64decode(b64data)
    content_type = "image/svg+xml" if obj.fmt == "svg" else "image/png"
    resp = HttpResponse(raw, content_type=content_type)
    if download:
        fname = f"qr.{ 'svg' if obj.fmt=='svg' else 'png' }"
        resp["Content-Disposition"] = f'attachment; filename="{fname}"'
    return resp
