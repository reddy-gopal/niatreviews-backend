from django.db import models


class Campus(models.Model):
    """Campus directory for NIAT; referenced by Founding Editor profile and articles."""
    name = models.CharField(max_length=200)
    short_name = models.CharField(max_length=100, blank=True, null=True)
    location = models.CharField(max_length=200)
    state = models.CharField(max_length=100)
    image_url = models.URLField(max_length=500)
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
