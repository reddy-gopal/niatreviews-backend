from django.core.cache import cache
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User


class HealthCheckView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        try:
            User.objects.exists()
            db_status = "ok"
        except Exception:
            db_status = "error"

        try:
            cache.set("healthcheck", "ok", timeout=5)
            cache_status = "ok" if cache.get("healthcheck") == "ok" else "error"
        except Exception:
            cache_status = "error"

        status_code = status.HTTP_200_OK if db_status == "ok" and cache_status == "ok" else status.HTTP_503_SERVICE_UNAVAILABLE
        return Response(
            {
                "status": "ok" if status_code == status.HTTP_200_OK else "error",
                "db": db_status,
                "cache": cache_status,
            },
            status=status_code,
        )
