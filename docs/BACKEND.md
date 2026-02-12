# NIATReviews.com — Backend Implementation

Django backend for the NIATReviews community platform (intermediate students post; verified NIAT seniors reply with threaded comments). Frontend: React.js. Target scale: ~2–3k concurrent users.

---

## 1. Stack & configuration

| Item | Choice |
|------|--------|
| Framework | Django 6.x |
| API | Django REST Framework |
| CORS | django-cors-headers |
| Database | SQLite (dev); ready for PostgreSQL |
| Auth | Custom user model `accounts.User` (UUID PK) |
| Media | `MEDIA_ROOT` = `media/`, `MEDIA_URL` = `/media/` |

**Key settings** (`backend/settings.py`):

- `AUTH_USER_MODEL = "accounts.User"`
- `INSTALLED_APPS`: accounts, verification, community, notifications, moderation, reviews, activity, rest_framework, corsheaders
- `ALLOWED_HOSTS = ['*']` (tighten in production)
- Scalability: comments note Redis/Celery/cursor pagination for future use

**Root URLs** (`backend/urls.py`):

- `/admin/` — Django admin
- `/api/` — includes `community.urls` (only community exposes REST API)
- In DEBUG: `/media/` serves `MEDIA_ROOT`

---

## 2. Project structure

```
backend/
├── backend/           # Project package
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── accounts/          # User model, roles, phone
├── verification/      # Senior + phone verification
├── community/         # Posts, comments, upvotes, categories, tags — only app with REST API
├── notifications/     # Notification types, notifications, delivery log
├── moderation/        # Featured posts, pending approval queue
├── reviews/           # Scaffold: Program, PartnerCollege, Review
├── activity/          # Engagement logs (optional metrics)
├── media/             # Uploaded files (e.g. post images)
├── manage.py
├── requirements.txt
└── docs/
    └── BACKEND.md     # This file
```

---

## 3. Apps and models

### 3.1 accounts

**Purpose:** Custom user, roles, phone (with verification flag).

| Model | Description |
|-------|-------------|
| **User** | Extends `AbstractUser`. UUID PK, `username`, `email`, `role` (student/senior/admin), `is_verified_senior`, `phone_number`, `phone_verified`. Indexes on username, email, is_verified_senior, phone_verified. |

**API:** No DRF routes; `UserSerializer` used by community (nested in Post/Comment). Admin: `UserAdmin` with role/phone fields.

---

### 3.2 verification

**Purpose:** Senior verification workflow and phone OTP verification.

| Model | Description |
|-------|-------------|
| **PhoneVerification** | UUID PK. `phone_number`, `otp_code`, `user` (optional), `expires_at`, `verified_at`, `created_at`. `is_expired` property. |
| **SeniorProfile** | UUID PK. OneToOne to User. `proof_summary`, `status` (pending/approved/rejected), `reviewed_by`, `reviewed_at`, `admin_notes`, timestamps. |

**Signals** (`verification.signals`, loaded in `VerificationConfig.ready`):

- `post_save` **SeniorProfile** → set `User.is_verified_senior = True` when `status == "approved"`.
- `post_save` **PhoneVerification** → when `verified_at` and `user` set, set `User.phone_number` and `User.phone_verified = True`.

**API:** No DRF routes. Admin: SeniorProfile, PhoneVerification.

---

### 3.3 community

**Purpose:** Posts, threaded comments, upvotes, categories, tags. Only app with public REST API.

| Model | Description |
|-------|-------------|
| **Category** | UUID PK. `name`, `slug`, `description`, `created_at`. |
| **Tag** | UUID PK. `name`, `slug`, `created_at`. |
| **Post** | UUID PK. `title`, `description`, `image`, `author` (User), `category`, M2M `tags`, `upvote_count`, `comment_count`, `is_published`, timestamps. Indexes: -created_at, (is_published, -created_at). |
| **Comment** | UUID PK. `post`, `author`, `parent` (self FK; null = top-level), `body`, `upvote_count`, timestamps. Indexes: (post, created_at), parent. |
| **PostUpvote** | UUID PK. `post`, `user`. UniqueConstraint (post, user). |
| **CommentUpvote** | UUID PK. `comment`, `user`. UniqueConstraint (comment, user). |

**Signals** (`community.signals`, loaded in `CommunityConfig.ready`):

- **PostUpvote** post_save → increment `Post.upvote_count`; post_delete → decrement (floor 0).
- **CommentUpvote** post_save → increment `Comment.upvote_count` for that comment only; post_delete → decrement (floor 0). Debug logging logs `comment_id`.
- **Comment** post_save (created, parent is None) → increment `Post.comment_count`; post_delete (parent is None) → decrement (floor 0).

**Serializers:**

- `CategorySerializer`, `TagSerializer` — full model.
- `PostSerializer` — author (UserSerializer), category, tags (nested read-only); read_only upvote_count, comment_count.
- `CommentMinimalSerializer` — id, body, author, created_at.
- `CommentSerializer` — author, parent (CommentMinimalSerializer read_only), post, body; read_only upvote_count; create sets author from request.
- `PostUpvoteSerializer` — post, user; create sets user from request.
- `CommentUpvoteSerializer` — comment (optional from body; overridden by context when comment from URL); validate() requires comment from body when not in context; create uses exact comment (no parent/reply mix-up).

**ViewSets:**

- `CategoryViewSet`, `TagViewSet` — full CRUD.
- `PostViewSet` — list/detail/create/update/delete; select_related author, category; prefetch_related tags.
- `CommentViewSet` — full CRUD; select_related author, parent; prefetch_related replies. Custom action: **upvote** (detail): `POST` add upvote, `DELETE` remove; comment is the one in URL (`/api/comments/<pk>/upvote/`).
- `CommentUpvoteViewSet` — list/create/destroy; get_serializer_context can pass `comment` from `comment_id` kwarg; perform_create logs comment_id and user_id.

**API routes (all under `/api/`):**

- `GET/POST /api/categories/`, `GET/PUT/PATCH/DELETE /api/categories/<id>/`
- `GET/POST /api/tags/`, `GET/PUT/PATCH/DELETE /api/tags/<id>/`
- `GET/POST /api/posts/`, `GET/PUT/PATCH/DELETE /api/posts/<id>/`
- `GET/POST /api/comments/`, `GET/PUT/PATCH/DELETE /api/comments/<id>/`
- `POST /api/comments/<id>/upvote/` — add upvote for that comment (reply or parent). `DELETE` — remove.
- `GET/POST /api/comment-upvotes/`, `GET/DELETE /api/comment-upvotes/<id>/`

**Comment upvote behaviour:** The comment upvoted is either the `pk` in the URL (recommended) or the `comment` id in the body for `POST /api/comment-upvotes/`. Reply vs parent is determined only by which id is sent; signals update only that comment’s `upvote_count`.

**Admin:** Category, Tag, Post, Comment, PostUpvote, CommentUpvote (list_display, filters, raw_id_fields, readonly counters).

**Tests:** `community.tests.CommentUpvoteReplyTest` — upvoting reply only increments reply’s count; parent only parent’s; both independent.

---

### 3.4 notifications

**Purpose:** In-app notifications and delivery log (email/push).

| Model | Description |
|-------|-------------|
| **NotificationType** | UUID PK. `code`, `name`, `description`, `email_template`, `push_template`, `created_at`. |
| **Notification** | UUID PK. `recipient`, `actor`, `verb`, `notification_type`, ContentType + `object_id` (GenericForeignKey `target`), `read_at`, `created_at`. Indexes: (recipient, -created_at), (recipient, read_at). |
| **NotificationDelivery** | UUID PK. `notification`, `channel` (email/push/in_app), `external_id`, `sent_at`, `opened_at`, `error_message`, `created_at`. |

**API:** No DRF routes. Admin: NotificationType, Notification, NotificationDelivery.

---

### 3.5 moderation

**Purpose:** Featured posts and generic approval queue.

| Model | Description |
|-------|-------------|
| **FeaturedPost** | UUID PK. FK to `community.Post`, `order`, `featured_at`, `featured_by` (User). |
| **PendingApprovalQueue** | UUID PK. ContentType + `object_id` (GenericForeignKey), `status` (pending/in_review/approved/rejected), `assigned_to`, `resolved_by`, `resolved_at`, `notes`, timestamps. |

**API:** No DRF routes. Admin: FeaturedPost, PendingApprovalQueue.

---

### 3.6 reviews (scaffold)

**Purpose:** Future program/college reviews.

| Model | Description |
|-------|-------------|
| **Program** | UUID PK. `name`, `slug`, `description`, timestamps. |
| **PartnerCollege** | UUID PK. `name`, `slug`, M2M to Program, timestamps. |
| **Review** | UUID PK. `author`, `program`, `partner_college`, timestamps. |

**API:** No DRF routes. Admin: Program, PartnerCollege, Review.

---

### 3.7 activity

**Purpose:** Optional engagement logs (views, clicks).

| Model | Description |
|-------|-------------|
| **EngagementLog** | UUID PK. Optional `user`, `action`, ContentType + `object_id` (GenericForeignKey), `session_key`, `created_at`. |

**API:** No DRF routes. Admin: EngagementLog.

---

## 4. API summary (community only)

Base URL: `/api/` (prefix from `backend.urls`).

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET, POST | `/categories/` | List, create categories |
| GET, PUT, PATCH, DELETE | `/categories/<id>/` | Retrieve, update, delete category |
| GET, POST | `/tags/` | List, create tags |
| GET, PUT, PATCH, DELETE | `/tags/<id>/` | Retrieve, update, delete tag |
| GET, POST | `/posts/` | List, create posts |
| GET, PUT, PATCH, DELETE | `/posts/<id>/` | Retrieve, update, delete post |
| GET, POST | `/comments/` | List, create comments |
| GET, PUT, PATCH, DELETE | `/comments/<id>/` | Retrieve, update, delete comment |
| POST | `/comments/<id>/upvote/` | Add upvote for comment `<id>` (reply or parent) |
| DELETE | `/comments/<id>/upvote/` | Remove upvote for comment `<id>` |
| GET, POST | `/comment-upvotes/` | List, create comment upvotes (body: `{"comment": "<uuid>"}`) |
| GET, DELETE | `/comment-upvotes/<id>/` | Retrieve, delete comment upvote |

All IDs are UUIDs. Authentication: use DRF auth (e.g. Session or Token) as configured; create/upvote require authenticated user.

---

## 5. Dependencies

From `requirements.txt`:

```
Django>=4.2,<6
djangorestframework>=3.14
django-cors-headers>=4.3
pillow>=10.0
```

---

## 6. Run / test

```bash
cd backend
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
# Admin: http://localhost:8000/admin/
# API:    http://localhost:8000/api/
```

```bash
python manage.py test community.tests.CommentUpvoteReplyTest
```

---

## 7. Design notes

- **UUIDs:** Primary keys are UUIDs across apps for non-sequential IDs and easier distribution.
- **Denormalized counts:** Post/Comment upvote and comment counts kept in DB and updated by signals; can later move to Redis/cache and async recalc.
- **Comment upvotes:** Reply vs parent is determined only by which comment id is used (URL or body); serializer and signals ensure only that comment’s count changes.
- **Verification:** Senior status and phone verification are driven by verification app models and signals; no REST API for verification in this doc.
- **Scalability:** Ready for Redis (CACHES, sessions), Celery, and cursor-based pagination as noted in settings.

This document reflects the current implementation as of the last update.
