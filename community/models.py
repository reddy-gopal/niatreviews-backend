"""
NIATReviews.com — Community app.
Posts (by students), threaded comments (by verified seniors only — enforce in API),
upvotes, categories, tags. UUID PKs and indexes for scale.
"""
import uuid
from django.conf import settings
from django.db import models


class Category(models.Model):
    """Broad category for posts (e.g. Admissions, Placements)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True, db_index=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "community_category"
        ordering = ["name"]
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


class Tag(models.Model):
    """Tag for posts; many-to-many via Post.tags."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50, unique=True, db_index=True)
    slug = models.SlugField(max_length=50, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "community_tag"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Post(models.Model):
    """
    Post by a user (Any user). Counters denormalized for list/filter performance;
    consider Redis/cache for high write volume; recalc via async task if needed.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255, db_index=True)
    slug = models.SlugField(max_length=300, unique=True, db_index=True)
    description = models.TextField()
    image = models.ImageField(upload_to="posts/", null=True, blank=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="community_posts",
        db_index=True,
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="posts",
        db_index=True,
    )
    tags = models.ManyToManyField(Tag, related_name="posts", blank=True, db_table="community_post_tags")

    # Denormalized counters for pagination/sorting; keep in sync via signals or async
    upvote_count = models.PositiveIntegerField(default=0, db_index=True)
    downvote_count = models.PositiveIntegerField(default=0, db_index=True)
    comment_count = models.PositiveIntegerField(default=0, db_index=True)

    is_published = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "community_post"
        indexes = [
            models.Index(fields=["-created_at"]),
            models.Index(fields=["is_published", "-created_at"]),
        ]
        ordering = ["-created_at"]
        verbose_name = "Post"
        verbose_name_plural = "Posts"

    def __str__(self):
        return self.title[:50]


class Comment(models.Model):
    """
    Threaded comment: parent is None for top-level, or the direct parent comment.
    Anyone can create a comment and reply to it.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="comments",
        db_index=True,
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="community_comments",
        db_index=True,
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="replies",
        db_index=True,
        help_text="Set for nested replies; null for top-level.",
    )
    body = models.TextField()
    # Denormalized count for display
    upvote_count = models.PositiveIntegerField(default=0, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "community_comment"
        indexes = [
            models.Index(fields=["post", "created_at"]),
            models.Index(fields=["parent"]),
        ]
        ordering = ["created_at"]
        verbose_name = "Comment"
        verbose_name_plural = "Comments"

    def __str__(self):
        return self.body[:50] or str(self.id)

class PostVote(models.Model):
    """
    One vote per user per post: value 1 (upvote) or -1 (downvote).
    Replaces PostUpvote for a single scalable table; counts kept in sync via signals.
    """
    VALUE_UP = 1
    VALUE_DOWN = -1
    VALUE_CHOICES = [(VALUE_UP, "upvote"), (VALUE_DOWN, "downvote")]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="votes",
        db_index=True,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="post_votes",
        db_index=True,
    )
    value = models.SmallIntegerField(choices=VALUE_CHOICES, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "community_post_vote"
        constraints = [
            models.UniqueConstraint(fields=["post", "user"], name="community_post_vote_unique_user_post"),
            models.CheckConstraint(check=models.Q(value__in=(1, -1)), name="community_post_vote_value_check"),
        ]
        indexes = [
            models.Index(fields=["post", "user"]),
            models.Index(fields=["post", "value"]),
        ]
        verbose_name = "Post vote"
        verbose_name_plural = "Post votes"

    def __str__(self):
        return f"Vote({self.user_id}, {self.post_id}, {self.value})"


class CommentUpvote(models.Model):
    """One upvote per user per comment. Unique constraint prevents duplicates."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    comment = models.ForeignKey(
        Comment,
        on_delete=models.CASCADE,
        related_name="upvotes",
        db_index=True,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="comment_upvotes",
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "community_comment_upvote"
        constraints = [
            models.UniqueConstraint(fields=["comment", "user"], name="community_comment_upvote_unique_user_comment"),
        ]
        indexes = [
            models.Index(fields=["comment", "user"]),
        ]
        verbose_name = "Comment upvote"
        verbose_name_plural = "Comment upvotes"

   
    def __str__(self):
        return f"Upvote({self.user_id}, {self.comment_id})"
