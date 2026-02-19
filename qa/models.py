"""
NIAT Q&A app.
Prospective students ask questions; verified seniors can each give one answer per question (multiple answers per question).
Anyone can upvote/downvote questions and answers.
"""
import re
import uuid
import logging
from django.conf import settings
from django.db import models, connection

logger = logging.getLogger(__name__)

# FTS5 virtual table name (must match migration).
# To inspect: Django shell: from django.db import connection; c = connection.cursor(); c.execute("SELECT rowid, title FROM qa_question_search LIMIT 5"); c.fetchall()
# Or: sqlite3 db.sqlite3 then ".tables" and "SELECT * FROM qa_question_search LIMIT 5"
FTS_QUESTION_SEARCH_TABLE = "qa_question_search"
QUESTION_TABLE = "qa_question"


# Common words to exclude from AND-query so we require substantive terms (e.g. "niat", "job", "scholarships").
# Includes question verbs that often don't appear in stored titles ("Does NIAT provide X?" vs "Are there X at NIAT?").
# If the user query becomes empty after stripping these, we fall back to using all tokens.
FTS5_STOPWORDS = frozenset({
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "can", "could",
    "me", "my", "i", "you", "we", "they", "it", "its", "this", "that",
    "to", "into", "for", "of", "in", "on", "at", "by", "with", "out", "from",
    "how", "what", "when", "where", "why", "which", "who", "and", "or", "but",
    "get", "got", "if", "so", "as", "than", "then", "just", "really",
    # Question-style verbs that may not appear in the stored question text:
    "provide", "provides", "provided", "providing", "offer", "offers", "offered", "offering",
    "give", "gives", "gave", "given", "giving", "help", "helps", "helped", "helping",
})

# Max terms in AND query so we don't require 10 words (e.g. "how can niat seniors help me get into job" -> cap at 5).
FTS5_MAX_AND_TERMS = 6


def build_fts5_query(user_phrase: str) -> str:
    """
    Build a safe FTS5 MATCH query from user input with prefix matching.
    - Lowercases and strips input; removes punctuation/special chars so contractions don't break matching.
    - Tokenizes, drops stopwords, then turns each remaining token into a prefix term (token*).
    - Prefix terms match singular/plural and variations (e.g. placement* matches "placement", "placements").
    - Terms are combined with AND. Returns empty string if no tokens (caller returns no results).
    """
    if not user_phrase or not isinstance(user_phrase, str):
        return ""
    # Normalize: lowercase, strip, length cap
    s = user_phrase.strip()[:500].lower()
    if not s:
        return ""
    # Remove punctuation and special characters so contractions and punctuation do not break token matching
    s = re.sub(r"[^\w\s]", " ", s, flags=re.UNICODE)
    tokens = [t for t in s.split() if t]
    if not tokens:
        return ""
    # Remove stopwords
    meaningful = [t for t in tokens if t not in FTS5_STOPWORDS]
    terms = meaningful if meaningful else tokens
    terms = terms[:FTS5_MAX_AND_TERMS]
    # Build prefix MATCH: each term becomes "term"* so FTS5 matches any token starting with that term
    escaped = [t.replace('"', '""') for t in terms]
    return " AND ".join(f'"{t}"*' for t in escaped)


class QuestionQuerySet(models.QuerySet):
    """QuerySet with FTS5 full-text search for SQLite."""

    def full_text_search(self, phrase):
        """
        Return questions matching the FTS5 phrase (SQLite only).
        Uses prefix-based MATCH (e.g. "niat"* AND "placement"*) for pluralization-tolerant search.
        Query is built by build_fts5_query(); parameter substitution prevents SQL injection.
        """
        if not phrase or not isinstance(phrase, str):
            return self.none()
        phrase = phrase.strip()
        if not phrase:
            return self.none()
        if connection.vendor != "sqlite":
            return self.none()
        fts_query = build_fts5_query(phrase)
        if not fts_query:
            return self.none()
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"SELECT id FROM {QUESTION_TABLE} WHERE rowid IN ("
                    f"SELECT rowid FROM {FTS_QUESTION_SEARCH_TABLE} WHERE {FTS_QUESTION_SEARCH_TABLE} MATCH %s)",
                    [fts_query],
                )
                ids = [row[0] for row in cursor.fetchall()]
        except Exception as e:
            logger.warning("FTS5 search failed: %s", e)
            return self.none()
        if not ids:
            return self.none()
        return self.filter(id__in=ids)


class QuestionManager(models.Manager):
    def get_queryset(self):
        return QuestionQuerySet(self.model, using=self._db)

    def search(self, q):
        """Return queryset of questions matching full-text phrase q (SQLite FTS5)."""
        return self.get_queryset().full_text_search(q)


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

    objects = QuestionManager()

    class Meta:
        db_table = "qa_question"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["is_faq", "faq_order"]),
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
    """Thread-style follow-up comment under an answered question. Only question author can create."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="followups",
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
        indexes = [models.Index(fields=["question", "created_at"])]

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
