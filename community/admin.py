from django.contrib import admin
from .models import Category, Tag, Post, Comment, PostVote, CommentUpvote


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "created_at")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("name",)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "created_at")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "category", "upvote_count", "downvote_count", "comment_count", "is_published", "created_at")
    list_filter = ("is_published", "category")
    search_fields = ("title", "description")
    raw_id_fields = ("author",)
    filter_horizontal = ("tags",)
    readonly_fields = ("upvote_count", "downvote_count", "comment_count")


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("post", "author", "parent", "upvote_count", "created_at")
    list_filter = ("post",)
    search_fields = ("body",)
    raw_id_fields = ("author", "parent")


@admin.register(PostVote)
class PostVoteAdmin(admin.ModelAdmin):
    list_display = ("post", "user", "value", "created_at")
    list_filter = ("value",)
    raw_id_fields = ("post", "user")


@admin.register(CommentUpvote)
class CommentUpvoteAdmin(admin.ModelAdmin):
    list_display = ("comment", "user", "created_at")
    raw_id_fields = ("comment", "user")
