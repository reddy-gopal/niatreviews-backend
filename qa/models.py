"""
NIAT Q&A app.
Prospective students ask questions; verified seniors can each give one answer per question (multiple answers per question).
Anyone can upvote/downvote questions and answers.
"""
import uuid
from django.conf import settings
from django.db import models
from django.contrib.postgres.search import SearchVectorField
from django.contrib.postgres.indexes import GinIndex


class Question(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="questions",
        db_index=True,
    )
    title = models.CharField(max_length=300)
    slug = models.SlugField(unique=True, max_length=350, db_index=True)
    body = models.TextField(blank=True)
    category = models.CharField(max_length=80, default="General", db_index=True)
    category_confidence = models.FloatField(default=0.0)
    category_source = models.CharField(max_length=20, default="keyword")
    is_answered = models.BooleanField(default=False, db_index=True)
    upvote_count = models.IntegerField(default=0, db_index=True)
    downvote_count = models.IntegerField(default=0, db_index=True)
    view_count = models.IntegerField(default=0, db_index=True)
    is_faq = models.BooleanField(default=False, db_index=True)
    faq_order = models.IntegerField(default=0, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    search_vector = SearchVectorField(null=True, blank=True)

    class Meta:
        db_table = "qa_question"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["is_faq", "faq_order"]),
            GinIndex(fields=["search_vector"], name="question_search_vector_gin_idx"),
            GinIndex(fields=["title"], name="question_title_trgm_idx", opclasses=["gin_trgm_ops"]),
        ]

    def save(self, *args, **kwargs):
        if self._state.adding:
            from qa.category_classifier import classifier
            text = f"{self.title}\n{self.body or ''}".strip()
            result = classifier.classify(text)
            self.category = result.get("category", "General")
            self.category_confidence = result.get("confidence", 0.0)
            self.category_source = result.get("source", "keyword")
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title[:80]


class Answer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="answers",
        db_index=True,
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="answers",
        db_index=True,
    )
    body = models.TextField()
    upvote_count = models.IntegerField(default=0, db_index=True)
    downvote_count = models.IntegerField(default=0, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "qa_answer"
        ordering = ["created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["question", "author"],
                name="qa_answer_one_per_senior_per_question",
            ),
        ]

    def __str__(self):
        return self.body[:50] or str(self.id)


class FollowUp(models.Model):
    """Reddit-style thread under an answer: top-level = student follow-up (question), replies = nested."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="followups",
        db_index=True,
    )
    answer = models.ForeignKey(
        Answer,
        on_delete=models.CASCADE,
        related_name="followups",
        db_index=True,
        null=True,
        blank=True,
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        related_name="replies",
        null=True,
        blank=True,
        db_index=True,
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="followups",
        db_index=True,
    )
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "qa_followup"
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["question", "created_at"]),
            models.Index(fields=["answer", "created_at"]),
        ]

    def __str__(self):
        return self.body[:50] or str(self.id)


class QuestionVote(models.Model):
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="votes",
        db_index=True,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="question_votes",
        db_index=True,
    )
    value = models.SmallIntegerField(db_index=True)  # 1 or -1

    class Meta:
        db_table = "qa_question_vote"
        constraints = [
            models.UniqueConstraint(fields=["question", "user"], name="qa_question_vote_unique"),
            models.CheckConstraint(check=models.Q(value__in=(1, -1)), name="qa_question_vote_value_check"),
        ]

    def __str__(self):
        return f"Vote({self.user_id}, {self.question_id}, {self.value})"


class AnswerVote(models.Model):
    answer = models.ForeignKey(
        Answer,
        on_delete=models.CASCADE,
        related_name="votes",
        db_index=True,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="answer_votes",
        db_index=True,
    )
    value = models.SmallIntegerField(db_index=True)  # 1 or -1

    class Meta:
        db_table = "qa_answer_vote"
        constraints = [
            models.UniqueConstraint(fields=["answer", "user"], name="qa_answer_vote_unique"),
            models.CheckConstraint(check=models.Q(value__in=(1, -1)), name="qa_answer_vote_value_check"),
        ]

    def __str__(self):
        return f"Vote({self.user_id}, {self.answer_id}, {self.value})"
