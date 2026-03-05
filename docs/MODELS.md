# Backend Models Reference

Documentation of Django models from the **accounts**, **articles**, and **campuses** apps.

---

## accounts

### User

Custom user with UUID primary key. Extends Django’s `AbstractUser`. Used for NIATReviews.com: roles, verified-senior flag, and optional phone (with verification).

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUIDField (PK) | Public UUID; default `uuid.uuid4`, not editable. Use in APIs and FKs. |
| `email` | EmailField | Optional, unique, indexed. |
| `username` | (inherited) | From AbstractUser. |
| `role` | CharField(20) | One of: `student`, `senior`, `admin`, `moderator`, `founding_editor`. Default: `student`. Indexed. |
| `is_verified_senior` | BooleanField | True when verification.SeniorProfile has been approved. Indexed. |
| `phone_number` | CharField(20) | E.164 or national format; optional, unique when set. Indexed. |
| `phone_verified` | BooleanField | True after successful phone OTP verification. Indexed. |

**Meta:** `db_table = "accounts_user"`  
**Indexes:** `username`, `(is_verified_senior, is_active)`, `phone_verified`.

---

### FoundingEditorProfile

One-to-one profile for Founding Editors (NIATVerse). Stores campus, LinkedIn, and year joined.

| Field | Type | Description |
|-------|------|-------------|
| `user` | OneToOneField(User) | PK; CASCADE delete. `related_name="founding_editor_profile"`. |
| `linkedin_profile` | URLField(500) | LinkedIn profile URL. Optional. |
| `campus_id` | IntegerField | Default campus for articles; matches campus list in frontend. Optional. |
| `campus_name` | CharField(200) | Campus display name (e.g. from frontend list). Optional. |
| `year_joined` | IntegerField | Year the student joined (e.g. 2024). Optional. |

**Meta:** `db_table = "accounts_founding_editor_profile"`.

---

## articles

### Category

Section categories for articles. Seeded with 6 default sections.

| Field | Type | Description |
|-------|------|-------------|
| `id` | AutoField (PK) | Default. |
| `name` | CharField(120) | Display name. |
| `slug` | SlugField(80) | Unique slug. |

**Meta:** `db_table = "articles_category"`, `ordering = ["id"]`.

**Category choices (slug → label):**  
`onboarding-kit`, `survival-food`, `club-directory`, `career-wins`, `local-travel`, `amenities`.

---

### Subcategory

Subcategories for categories that need them (e.g. Club Directory, Amenities). Admin-managed.

| Field | Type | Description |
|-------|------|-------------|
| `id` | AutoField (PK) | Default. |
| `category` | ForeignKey(Category) | CASCADE, `related_name="subcategories"`. Indexed. |
| `slug` | SlugField(80) | Unique per category. |
| `label` | CharField(120) | Display name. |
| `requires_other` | BooleanField | If True, `subcategory_other` is required (e.g. “Others” with custom name). Default: False. |
| `display_order` | PositiveSmallIntegerField | Order in lists (lower first). Default: 0. |

**Meta:** `db_table = "articles_subcategory"`, `ordering = ["category", "display_order", "slug"]`, `unique_together = [("category", "slug")]`.

---

### Article

Main article/content model. Author and campus stored as denormalized IDs/names; category also has FK.

| Field | Type | Description |
|-------|------|-------------|
| `id` | AutoField (PK) | Default. |
| `author_id` | CharField(36) | User UUID. Indexed. |
| `author_username` | CharField(150) | Denormalized. |
| `campus_id` | IntegerField | Optional. |
| `campus_name` | CharField(200) | Optional. |
| `category` | CharField(50) | One of CATEGORY_CHOICES (slug). |
| `category_fk` | ForeignKey(Category) | SET_NULL, optional, `related_name="articles"`, `db_column="category_id"`. |
| `title` | CharField(500) | |
| `slug` | SlugField(600) | Unique. |
| `excerpt` | TextField(1000) | |
| `body` | TextField | |
| `cover_image` | URLField | Optional. |
| `images` | JSONField | List of image URLs from body. Default: `[]`. |
| `status` | CharField(20) | One of: `draft`, `pending_review`, `published`, `rejected`. Default: `pending_review`. |
| `featured` | BooleanField | Default: False. |
| `helpful_count` | PositiveIntegerField | Default: 0. |
| `is_global_guide` | BooleanField | Default: False. |
| `topic` | CharField(50) | One of GUIDE_TOPIC_CHOICES. Optional. |
| `club_id` | IntegerField | Optional. |
| `subcategory` | CharField(80) | Club Directory subcategory slug (e.g. media-club, coding-club, others). Indexed. Optional. |
| `subcategory_other` | CharField(200) | Custom name when subcategory is “others”. Optional. |
| `rejection_reason` | TextField | Optional. |
| `reviewed_by_id` | CharField(36) | Optional. |
| `reviewed_at` | DateTimeField | Optional. |
| `published_at` | DateTimeField | Optional. |
| `created_at` | DateTimeField | `auto_now_add`. |
| `updated_at` | DateTimeField | `auto_now`. |

**Meta:** `ordering = ["-created_at"]`.  
**Indexes:** `(status, campus_id)`, `(status, is_global_guide)`, `(status, category)`, `author_id`.

**Guide topic choices:** Placements, Open Source, Internships, Competitive Programming, GSoC, Skills.

---

### ArticleHelpful

Records a single “helpful” vote per user per article.

| Field | Type | Description |
|-------|------|-------------|
| `id` | AutoField (PK) | Default. |
| `article` | ForeignKey(Article) | CASCADE, `related_name="helpful_votes"`. |
| `user_id` | CharField(36) | User UUID. |
| `created_at` | DateTimeField | `auto_now_add`. |

**Meta:** UniqueConstraint on `(article, user_id)` → `articles_articlehelpful_unique`.

---

### ArticleComment

Comment on an article. Author stored as ID and username.

| Field | Type | Description |
|-------|------|-------------|
| `id` | AutoField (PK) | Default. |
| `article` | ForeignKey(Article) | CASCADE, `related_name="comments"`. |
| `author_id` | CharField(36) | User UUID. |
| `author_username` | CharField(150) | Denormalized. |
| `body` | TextField(2000) | |
| `created_at` | DateTimeField | `auto_now_add`. |
| `is_visible` | BooleanField | Default: True. |

**Meta:** `ordering = ["created_at"]`.

---

## campuses

### Campus

Campus directory for NIAT; referenced by Founding Editor profile and articles.

| Field | Type | Description |
|-------|------|-------------|
| `id` | AutoField (PK) | Default. |
| `name` | CharField(200) | |
| `short_name` | CharField(100) | Optional. |
| `location` | CharField(200) | |
| `state` | CharField(100) | |
| `image_url` | URLField(500) | |
| `slug` | SlugField(120) | Unique. |
| `is_deemed` | BooleanField | Default: False. |
| `created_at` | DateTimeField | `auto_now_add`. |
| `updated_at` | DateTimeField | `auto_now`. |

**Meta:** `db_table = "campuses"`, `ordering = ["name"]`.

---

## Summary

| App | Models |
|-----|--------|
| **accounts** | User, FoundingEditorProfile |
| **articles** | Category, Subcategory, Article, ArticleHelpful, ArticleComment |
| **campuses** | Campus |
