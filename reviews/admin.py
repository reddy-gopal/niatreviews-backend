from django.contrib import admin
from .models import Program, PartnerCollege, Review, SeniorOnboardingReview


@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(PartnerCollege)
class PartnerCollegeAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    filter_horizontal = ("programs",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("author", "program", "partner_college", "created_at")
    raw_id_fields = ("author",)


@admin.register(SeniorOnboardingReview)
class SeniorOnboardingReviewAdmin(admin.ModelAdmin):
    list_display = ("user", "teaching_quality", "overall_satisfaction", "recommendation_score", "created_at")
    list_filter = ("created_at",)
    search_fields = ("user__username", "user__email")
    raw_id_fields = ("user",)
    readonly_fields = ("id", "created_at", "updated_at")
    fieldsets = (
        (None, {"fields": ("id", "user", "created_at", "updated_at")}),
        ("Education & Faculty", {"fields": ("teaching_quality", "faculty_support_text", "faculty_support_choice")}),
        ("Practical Learning", {"fields": ("projects_quality", "best_project_or_skill", "learning_balance_choice")}),
        ("Placements & Career", {"fields": ("placement_support", "job_ready_text", "placement_reality_choice")}),
        ("Overall Experience", {"fields": ("overall_satisfaction", "one_line_experience", "experience_feel_choice")}),
        ("Recommendation", {"fields": ("recommendation_score", "who_should_join_text", "final_recommendation_choice")}),
    )
