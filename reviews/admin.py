from django.contrib import admin
from .models import Program, PartnerCollege, Review


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
