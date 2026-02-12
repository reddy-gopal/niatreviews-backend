from django.contrib import admin
from .models import EngagementLog


@admin.register(EngagementLog)
class EngagementLogAdmin(admin.ModelAdmin):
    list_display = ("action", "content_type", "object_id", "user", "created_at")
    list_filter = ("action", "content_type")
    raw_id_fields = ("user",)
    date_hierarchy = "created_at"
    readonly_fields = ("created_at",)
