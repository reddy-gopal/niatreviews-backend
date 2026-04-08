from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("action", "actor", "target_user", "entity_type", "entity_id", "created_at")
    search_fields = ("actor__username", "target_user__username", "entity_type", "entity_id")
    list_filter = ("action", "entity_type", "created_at")
    raw_id_fields = ("actor", "target_user")
    readonly_fields = ("id", "created_at")
