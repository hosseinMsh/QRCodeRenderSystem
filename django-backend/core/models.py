import uuid
from django.db import models
from django.utils import timezone

class QRRender(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    options_hash = models.CharField(max_length=64, unique=True, db_index=True)
    # Original options JSON we sent to the Node service (normalized)
    options_json = models.JSONField()
    # "png" or "svg"
    fmt = models.CharField(max_length=8, default="png")
    # Always store base64 data URL (data:image/...;base64,xxxx)
    image_base64 = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.fmt}:{str(self.id)[:8]}... ({self.created_at.isoformat()})"
