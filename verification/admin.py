from django.contrib import admin
from .models import SeniorProfile, PhoneVerification


@admin.register(SeniorProfile)
class SeniorProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "status", "reviewed_by", "reviewed_at", "created_at")
    list_filter = ("status",)
    search_fields = ("user__username", "user__email", "proof_summary")
    raw_id_fields = ("user", "reviewed_by")
    readonly_fields = ("created_at", "updated_at")


@admin.register(PhoneVerification)
class PhoneVerificationAdmin(admin.ModelAdmin):
    list_display = ("phone_number", "user", "verified_at", "expires_at", "created_at")
    list_filter = ("verified_at",)
    search_fields = ("phone_number", "user__username")
    raw_id_fields = ("user",)
    readonly_fields = ("created_at",)
    date_hierarchy = "created_at"
