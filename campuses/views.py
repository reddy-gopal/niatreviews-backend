from django.db.models import Count
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from .models import Campus
from .serializers import CampusSerializer

class CampusListView(APIView):
    """GET /api/campuses/ — list all campuses ordered by article count descending."""

    def get(self, request):
        qs = Campus.objects.annotate(article_count=Count('articles')).order_by('-article_count', 'name')
        serializer = CampusSerializer(qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class CampusDetailView(APIView):
    """GET /api/campuses/<slug>/ — get campus details by slug."""

    def get(self, request, slug):
        try:
            campus = Campus.objects.annotate(article_count=Count('articles')).get(slug=slug)
            serializer = CampusSerializer(campus)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Campus.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
