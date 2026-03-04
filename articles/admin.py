from django.contrib import admin
from django.utils import timezone
from .models import Article, ArticleComment, Category, Subcategory


class SubcategoryInline(admin.TabularInline):
    model = Subcategory
    extra = 0
    ordering = ["display_order", "slug"]


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "slug")
    prepopulated_fields = {"slug": ["name"]}
    inlines = [SubcategoryInline]


@admin.register(Subcategory)
class SubcategoryAdmin(admin.ModelAdmin):
    list_display = ("category", "slug", "label", "requires_other", "display_order")
    list_filter = ("category",)
    search_fields = ("slug", "label")
    ordering = ["category", "display_order", "slug"]


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "author_username",
        "campus_name",
        "category",
        "subcategory",
        "subcategory_other",
        "status",
        "featured",
        "helpful_count",
        "created_at",
    )
    list_filter = ("status", "category", "subcategory", "is_global_guide", "featured")
    search_fields = ("title", "author_username", "campus_name")
    readonly_fields = (
        "author_id",
        "author_username",
        "slug",
        "helpful_count",
        "reviewed_by_id",
        "reviewed_at",
        "published_at",
        "created_at",
        "updated_at",
    )
    actions = ["publish_selected", "reject_selected"]

    def get_queryset(self, request):
        return super().get_queryset(request)

    def save_model(self, request, obj, form, change):
        obj.save()

    def delete_model(self, request, obj):
        obj.delete()

    def delete_queryset(self, request, queryset):
        queryset.delete()

    @admin.action(description="Publish selected")
    def publish_selected(self, request, queryset):
        for obj in queryset:
            obj.status = "published"
            obj.published_at = timezone.now()
            obj.reviewed_by_id = str(request.user.id)
            obj.reviewed_at = timezone.now()
            obj.save()
        self.message_user(request, f"Published {queryset.count()} article(s).")

    @admin.action(description="Reject selected")
    def reject_selected(self, request, queryset):
        for obj in queryset:
            obj.status = "rejected"
            obj.rejection_reason = "Rejected via admin bulk action."
            obj.reviewed_by_id = str(request.user.id)
            obj.reviewed_at = timezone.now()
            obj.save()
        self.message_user(request, f"Rejected {queryset.count()} article(s).")


@admin.register(ArticleComment)
class ArticleCommentAdmin(admin.ModelAdmin):
    list_display = ("article", "author_username", "body", "created_at", "is_visible")

    def get_queryset(self, request):
        return super().get_queryset(request)

    def save_model(self, request, obj, form, change):
        obj.save()

    def delete_model(self, request, obj):
        obj.delete()
