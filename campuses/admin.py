from django.contrib import admin
from .models import Campus


@admin.register(Campus)
class CampusAdmin(admin.ModelAdmin):
    list_display = ("name", "short_name", "location", "state", "slug", "is_deemed")
    list_filter = ("is_deemed", "state")
    search_fields = ("name", "location", "state")
