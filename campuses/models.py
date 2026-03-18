import uuid
from django.db import models


class Campus(models.Model):
    """Campus directory for NIAT; referenced by Founding Editor profile and articles."""
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        db_column="id_new"
    )
    name = models.CharField(max_length=200)
    short_name = models.CharField(max_length=100, blank=True, null=True)
    location = models.CharField(max_length=200)
    state = models.CharField(max_length=100)
    image_url = models.URLField(max_length=500)
    google_map_link = models.URLField(max_length=1000, blank=True, null=True)
    description = models.TextField(blank=True, default="")
    slug = models.SlugField(max_length=120, unique=True)
    is_deemed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "campuses"
        ordering = ["name"]
        verbose_name_plural = "Campuses"

    def __str__(self):
        return self.name
