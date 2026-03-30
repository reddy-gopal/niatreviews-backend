import uuid
from django.conf import settings
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

class Club(models.Model):
    """Club directory entity that can be shared across multiple campuses."""

    id = models.AutoField(primary_key=True)
    campuses = models.ManyToManyField(
        "campuses.Campus",
        through="ClubCampus",
        related_name="clubs",
        blank=True,
    )
    name = models.CharField(max_length=160)
    slug = models.SlugField(max_length=120, unique=True)
    objective = models.TextField(blank=True)
    logo_url = models.URLField(blank=True)
    cover_image = models.URLField(blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "articles"
        db_table = "articles_club"
        ordering = ["name"]

    def __str__(self):
        return self.name


class ClubCampus(models.Model):
    """Campus chapter metadata for a club (one row per club-campus pair)."""

    club = models.ForeignKey(
        Club,
        on_delete=models.CASCADE,
        related_name="campus_chapters",
    )
    campus = models.ForeignKey(
        "campuses.Campus",
        on_delete=models.CASCADE,
        related_name="club_chapters",
    )

    member_count = models.PositiveIntegerField(default=0)
    open_to_all = models.BooleanField(default=True)

    president_name = models.CharField(max_length=255, blank=True)
    president_email = models.EmailField(blank=True)
    president_photo = models.ImageField(upload_to="club_leaders/", null=True, blank=True)
    vice_president_name = models.CharField(max_length=255, blank=True)
    vice_president_email = models.EmailField(blank=True)
    vice_president_photo = models.ImageField(upload_to="club_leaders/", null=True, blank=True)
    instagram = models.URLField(blank=True)
    linkedin = models.URLField(blank=True)

    chapter_description = models.TextField(blank=True)
    contact_email = models.EmailField(blank=True)
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "articles"
        db_table = "articles_club_campus"
        unique_together = [("club", "campus")]
        ordering = ["club__name"]

    def __str__(self):
        return f"{self.club.name} @ {self.campus.name}"


class Category(models.Model):
    """Section categories for articles. Seeded with 6 default sections."""
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        db_column="id_new"
    )
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
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        db_column="id_new"
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="subcategories",
        db_index=True,
    )
    campus = models.ForeignKey(
        "campuses.Campus",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
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
        ordering = ["category", "campus", "display_order", "slug"]
        unique_together = [("category", "campus", "slug")]
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
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        db_column="id_new"
    )
    author_id = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="articles",
        db_column="author_id",
    )
    author_username = models.CharField(max_length=150)
    campus_id = models.ForeignKey(
        "campuses.Campus",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="articles",
        db_column="campus_id",
    )
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
    upvote_count = models.PositiveIntegerField(default=0, db_index=True)
    view_count = models.PositiveIntegerField(default=0, db_index=True)
    ai_generated = models.BooleanField(default=False, db_index=True)
    is_global_guide = models.BooleanField(default=False)
    topic = models.CharField(max_length=50, choices=GUIDE_TOPIC_CHOICES, blank=True)
    # Club Directory subcategory: slug (e.g. media-club, coding-club, others); when "others", subcategory_other holds custom name
    subcategory = models.CharField(max_length=80, blank=True, db_index=True)
    subcategory_other = models.CharField(max_length=200, blank=True)
    meta_title = models.CharField(max_length = 255, blank = True)
    meta_description = models.TextField(blank = True)
    meta_keywords = models.JSONField(default=list, blank=True, help_text="SEO keywords list")
    rejection_reason = models.TextField(blank=True)
    reviewed_by_id = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_articles",
        db_column="reviewed_by_id",
    )
    ai_confident_score = models.FloatField(null = True, blank=True)
    ai_feedback = models.JSONField(null = True, blank=True)
    ai_reviewed_at = models.DateTimeField(null = True, blank=True)
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
            models.Index(fields=["campus_id", "category", "subcategory", "status"], name="art_camp_cat_sub_st_idx"),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not (self.slug or "").strip():
            self.slug = generate_unique_slug(self.title or "article", instance=self)
        super().save(*args, **kwargs)

    @classmethod
    def for_club_feed(cls, campus_id, club_slug, status="published"):
        return cls.objects.filter(
            campus_id=campus_id,
            category="club-directory",
            subcategory=club_slug,
            status=status,
        ).order_by("-published_at")


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


SUGGESTION_TYPE_CHOICES = [
    ("missing_info", "Missing Info"),
    ("outdated_content", "Outdated Content"),
    ("wrong_info", "Wrong Info"),
    ("add_club_or_facility", "Add a Club or Facility"),
    ("other", "Other"),
]


class ArticleUpvote(models.Model):
    """One upvote per user per article. Unique (article_id, user_id)."""
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    article = models.ForeignKey(
        Article,
        on_delete=models.CASCADE,
        related_name="upvotes",
        db_column="article_id",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="article_upvotes",
        db_column="user_id",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "articles"
        db_table = "articles_articleupvote"
        constraints = [
            models.UniqueConstraint(fields=["article", "user"], name="articles_articleupvote_article_user_uniq")
        ]
        indexes = [
            models.Index(fields=["article", "user"], name="articles_upv_article_user_idx"),
        ]


class ArticleSuggestion(models.Model):
    """Structured suggestion for an article. Not shown publicly; author/admin see via dashboard."""
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    article = models.ForeignKey(
        Article,
        on_delete=models.CASCADE,
        related_name="suggestions",
        db_column="article_id",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="article_suggestions",
        db_column="user_id",
    )
    type = models.CharField(max_length=32, choices=SUGGESTION_TYPE_CHOICES, db_index=True)
    content = models.CharField(max_length=150)
    is_anonymous = models.BooleanField(default=False)
    reviewed = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "articles"
        db_table = "articles_articlesuggestion"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["article"], name="articles_sugg_article_idx"),
            models.Index(fields=["reviewed", "created_at"], name="articles_sugg_rev_created_idx"),
        ]

