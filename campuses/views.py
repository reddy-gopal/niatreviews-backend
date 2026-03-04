from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from .models import Campus
from .serializers import CampusSerializer


class CampusListView(APIView):
    """GET /api/campuses/ — list all campuses ordered by name."""

    def get(self, request):
        try:
            qs = Campus.objects.all().order_by("name")
            serializer = CampusSerializer(qs, many=True)
            return Response(serializer.data)
        except Exception:
            return Response(
                {"detail": "Failed to load campuses."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
