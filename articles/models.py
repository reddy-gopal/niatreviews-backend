import uuid
from django.db import models
from django.utils.text import slugify

CATEGORY_CHOICES = [
    ("onboarding-kit", "The Onboarding Kit"),
    ("survival-food", "Survival & Food"),
    ("club-directory", "The Club Directory"),
    ("career-wins", "Career & Wins"),
    ("local-travel", "Local Travel & Hangout Spots"),
    ("amenities", "Amenities"),
]


class Category(models.Model):
    """Section categories for articles. Seeded with 6 default sections."""
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=80, unique=True)

    class Meta:
        app_label = "articles"
        db_table = "articles_category"
        ordering = ["id"]
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


class Subcategory(models.Model):
    """Subcategories for categories that need them (e.g. Club Directory, Amenities). Scalable and admin-managed."""
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="subcategories",
        db_index=True,
    )
    slug = models.SlugField(max_length=80)
    label = models.CharField(max_length=120, help_text="Display name")
    requires_other = models.BooleanField(
        default=False,
        help_text="If True, subcategory_other is required (e.g. 'Others' with custom name)",
    )
    display_order = models.PositiveSmallIntegerField(default=0, help_text="Order in lists (lower first)")

    class Meta:
        app_label = "articles"
        db_table = "articles_subcategory"
        ordering = ["category", "display_order", "slug"]
        unique_together = [("category", "slug")]
        verbose_name_plural = "Subcategories"

    def __str__(self):
        return f"{self.category.slug}: {self.label}"


GUIDE_TOPIC_CHOICES = [
    ("Placements", "Placements"),
    ("Open Source", "Open Source"),
    ("Internships", "Internships"),
    ("Competitive Programming", "Competitive Programming"),
    ("GSoC", "GSoC"),
    ("Skills", "Skills"),
]

STATUS_CHOICES = [
    ("draft", "Draft"),
    ("pending_review", "Pending Review"),
    ("published", "Published"),
    ("rejected", "Rejected"),
]


class Article(models.Model):
    author_id = models.CharField(max_length=36, db_index=True)
    author_username = models.CharField(max_length=150)
    campus_id = models.IntegerField(null=True, blank=True)
    campus_name = models.CharField(max_length=200, blank=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    category_fk = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="articles",
        db_column="category_id",
    )
    title = models.CharField(max_length=500)
    slug = models.SlugField(max_length=600, unique=True)
    excerpt = models.TextField(max_length=1000)
    body = models.TextField()
    cover_image = models.URLField(blank=True)
    images = models.JSONField(default=list, blank=True, help_text="List of image URLs from the article body")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending_review")
    featured = models.BooleanField(default=False)
    helpful_count = models.PositiveIntegerField(default=0)
    is_global_guide = models.BooleanField(default=False)
    topic = models.CharField(max_length=50, choices=GUIDE_TOPIC_CHOICES, blank=True)
    club_id = models.IntegerField(null=True, blank=True)
    # Club Directory subcategory: slug (e.g. media-club, coding-club, others); when "others", subcategory_other holds custom name
    subcategory = models.CharField(max_length=80, blank=True, db_index=True)
    subcategory_other = models.CharField(max_length=200, blank=True)
    rejection_reason = models.TextField(blank=True)
    reviewed_by_id = models.CharField(max_length=36, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "articles"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "campus_id"]),
            models.Index(fields=["status", "is_global_guide"]),
            models.Index(fields=["status", "category"]),
            models.Index(fields=["author_id"]),
        ]

    def __str__(self):
        return self.title


def generate_unique_slug(title, instance=None):
    base = slugify(title)[:500] or "article"
    suffix = uuid.uuid4().hex[:8]
    slug = f"{base}-{suffix}"
    if instance and instance.pk:
        qs = Article.objects.exclude(pk=instance.pk).filter(slug=slug)
    else:
        qs = Article.objects.filter(slug=slug)
    if qs.exists():
        return f"{base}-{uuid.uuid4().hex[:8]}"
    return slug


class ArticleHelpful(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name="helpful_votes")
    user_id = models.CharField(max_length=36)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "articles"
        constraints = [
            models.UniqueConstraint(fields=["article", "user_id"], name="articles_articlehelpful_unique")
        ]


class ArticleComment(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name="comments")
    author_id = models.CharField(max_length=36)
    author_username = models.CharField(max_length=150)
    body = models.TextField(max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True)
    is_visible = models.BooleanField(default=True)

    class Meta:
        app_label = "articles"
        ordering = ["created_at"]
