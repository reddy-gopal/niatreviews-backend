from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline
from .models import FeaturedPost, PendingApprovalQueue


@admin.register(FeaturedPost)
class FeaturedPostAdmin(admin.ModelAdmin):
    list_display = ("post", "order", "featured_at", "featured_by")
    raw_id_fields = ("post", "featured_by")


@admin.register(PendingApprovalQueue)
class PendingApprovalQueueAdmin(admin.ModelAdmin):
    list_display = ("content_type", "object_id", "status", "assigned_to", "created_at")
    list_filter = ("status", "content_type")
    raw_id_fields = ("assigned_to", "resolved_by")
