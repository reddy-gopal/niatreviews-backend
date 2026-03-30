from django.contrib import admin
from django.utils import timezone
from .models import Article, ArticleSuggestion, ArticleUpvote, Category, Club, ClubCampus, Subcategory


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
    list_display = ("label", "category", "campus", "slug", "requires_other", "display_order")
    list_filter = ("category", "campus")
    search_fields = ("label", "slug")
    ordering = ["category", "campus", "display_order", "slug"]


@admin.register(Club)
class ClubAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "is_active",
        "updated_at",
    )
    list_filter = ("is_active",)
    search_fields = ("name", "campuses__name", "objective")
    prepopulated_fields = {"slug": ["name"]}


@admin.register(ClubCampus)
class ClubCampusAdmin(admin.ModelAdmin):
    list_display = (
        "club",
        "campus",
        "member_count",
        "president_name",
        "vice_president_name",
        "is_active",
        "updated_at",
    )
    list_filter = ("campus", "club", "is_active", "open_to_all")
    search_fields = ("club__name", "club__slug", "campus__name", "president_name", "vice_president_name")


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
        "upvote_count",
        "view_count",
        "created_at",
    )
    list_filter = ("status", "category", "subcategory", "is_global_guide", "featured")
    search_fields = ("title", "author_username", "campus_name")
    readonly_fields = (
        "author_id",
        "author_username",
        "slug",
        "upvote_count",
        "view_count",
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
            obj.reviewed_by_id = request.user
            obj.reviewed_at = timezone.now()
            obj.save()
        self.message_user(request, f"Published {queryset.count()} article(s).")

    @admin.action(description="Reject selected")
    def reject_selected(self, request, queryset):
        for obj in queryset:
            obj.status = "rejected"
            obj.rejection_reason = "Rejected via admin bulk action."
            obj.reviewed_by_id = request.user
            obj.reviewed_at = timezone.now()
            obj.save()
        self.message_user(request, f"Rejected {queryset.count()} article(s).")


@admin.register(ArticleUpvote)
class ArticleUpvoteAdmin(admin.ModelAdmin):
    list_display = ("id", "article", "user", "created_at")
    list_filter = ("created_at",)
    search_fields = ("article__title", "user__username")
    readonly_fields = ("created_at",)


@admin.register(ArticleSuggestion)
class ArticleSuggestionAdmin(admin.ModelAdmin):
    list_display = ("id", "article", "type", "content", "is_anonymous", "reviewed", "created_at")
    list_filter = ("type", "reviewed", "created_at")
    search_fields = ("article__title", "content")
    readonly_fields = ("created_at",)
