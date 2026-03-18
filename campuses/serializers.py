from rest_framework import serializers
from .models import Campus


class CampusSerializer(serializers.ModelSerializer):
    """List campuses: id, name, shortName, location, state, imageUrl, slug, isDeemed, googleMapLink, description."""

    shortName = serializers.CharField(source="short_name", allow_null=True)
    imageUrl = serializers.URLField(source="image_url")
    isDeemed = serializers.BooleanField(source="is_deemed")
    googleMapLink = serializers.URLField(source="google_map_link", allow_null=True, required=False)

    class Meta:
        model = Campus
        fields = [
            "id",
            "name",
            "shortName",
            "location",
            "state",
            "imageUrl",
            "slug",
            "isDeemed",
            "googleMapLink",
            "description",
        ]
