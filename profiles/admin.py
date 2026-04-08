from django.contrib import admin

from .models import VerifiedNiatStudentProfile, IntermediateStudentProfile, NiatStudentProfile


@admin.register(IntermediateStudentProfile)
class IntermediateStudentProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "college_name", "branch", "created_at")
    search_fields = ("user__username", "user__email", "college_name", "branch")
    list_filter = ("branch", "created_at")
    raw_id_fields = ("user",)


@admin.register(NiatStudentProfile)
class NiatStudentProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "campus", "student_id_number", "status", "reviewed_by", "reviewed_at")
    search_fields = ("user__username", "user__email", "student_id_number")
    list_filter = ("status", "reviewed_at", "created_at")
    raw_id_fields = ("user", "reviewed_by", "campus")


@admin.register(VerifiedNiatStudentProfile)
class VerifiedNiatStudentProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "campus", "campus_name", "year_joined", "badge_awarded_at")
    search_fields = ("user__username", "user__email", "campus_name", "linkedin_profile")
    list_filter = ("campus_name", "badge_awarded_at")
    raw_id_fields = ("user", "campus")
