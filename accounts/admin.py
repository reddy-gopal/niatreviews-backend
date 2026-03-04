from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, FoundingEditorProfile


@admin.register(FoundingEditorProfile)
class FoundingEditorProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "campus_id", "campus_name", "year_joined", "linkedin_profile")
    search_fields = ("user__username", "linkedin_profile")


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        "username", "email", "phone_number", "phone_verified",
        "role", "is_verified_senior", "is_staff", "is_active", "date_joined",
    )
    list_filter = ("role", "is_verified_senior", "phone_verified", "is_staff", "is_active")
    search_fields = ("username", "email", "first_name", "last_name", "phone_number")
    ordering = ("-date_joined",)
    filter_horizontal = ()

    fieldsets = BaseUserAdmin.fieldsets + (
        ("NIAT", {"fields": ("role", "is_verified_senior")}),
        ("Phone", {"fields": ("phone_number", "phone_verified")}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ("NIAT", {"fields": ("role", "is_verified_senior")}),
        ("Phone", {"fields": ("phone_number", "phone_verified")}),
    )
