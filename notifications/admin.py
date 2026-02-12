from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline
from .models import NotificationType, Notification, NotificationDelivery


@admin.register(NotificationType)
class NotificationTypeAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "created_at")
    search_fields = ("code", "name")


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("recipient", "actor", "verb", "notification_type", "read_at", "created_at")
    list_filter = ("verb", "notification_type")
    raw_id_fields = ("recipient", "actor")
    readonly_fields = ("created_at",)
    date_hierarchy = "created_at"


class NotificationDeliveryInline(admin.TabularInline):
    model = NotificationDelivery
    extra = 0
    readonly_fields = ("created_at", "sent_at", "opened_at")


@admin.register(NotificationDelivery)
class NotificationDeliveryAdmin(admin.ModelAdmin):
    list_display = ("notification", "channel", "sent_at", "opened_at", "created_at")
    list_filter = ("channel",)
    raw_id_fields = ("notification",)
