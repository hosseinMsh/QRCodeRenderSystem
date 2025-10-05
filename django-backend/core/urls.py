from django.urls import path
from core.views import generate_qr

urlpatterns = [
    path("qr/", generate_qr, name="generate_qr"),
]
