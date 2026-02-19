"""
Auto category classification for Q&A questions.
Uses keyword scoring with optional Groq LLM; results cached for 7 days.
"""
import hashlib
import json
import logging
import re
from django.core.cache import cache
from django.conf import settings

logger = logging.getLogger(__name__)

# Set to True to print Groq request/response to console (runserver).
DEBUG_GROQ = getattr(settings, "DEBUG_GROQ_CLASSIFIER", True)


def _log(msg: str, *args) -> None:
    logger.info(msg, *args)
    if DEBUG_GROQ:
        print(f"[CategoryClassifier] {msg % args if args else msg}")

CATEGORIES = [
    "Scholarships & Fee",
    "Hostel & Accommodation",
    "Admissions & Eligibility",
    "Exam & Syllabus",
    "Campus Life",
    "Placements & Career",
    "Rules & Regulations",
    "Faculty & Academics",
    "General",
]

# Keywords per category (lowercase). Multi-word phrases get 2 points; single words 1.
# Order matters for tie-break: first category with highest score wins.
CATEGORY_KEYWORDS = {
    "Scholarships & Fee": [
        "scholarship", "scholarships", "fee", "fees", "tuition", "cost", "payment",
        "afford", "expensive", "cheap", "lakh", "lakhs", "rupee", "rupees", "price", "funding", "financial",
        "total fee", "hostel fee", "program fee", "merit-based", "renewal", "available at niat",
    ],
    "Hostel & Accommodation": [
        "hostel", "hostels", "hostel fee", "accommodation", "room", "rooms", "stay", "living",
        "mess", "food", "boarding", "residence", "pg", "rent", "occupancy", "occupancy room",
    ],
    "Admissions & Eligibility": [
        "admission", "admissions", "eligibility", "apply", "criteria", "cutoff", "cut off",
        "counseling", "counselling", "join", "enroll", "enrollment", "qualification",
        "12th", "class 12", "aggregate", "marks", "percentage", "guaranteed after",
        "choose which city", "choose city", "university want", "documents",
    ],
    "Exam & Syllabus": [
        "exam", "exams", "syllabus", "curriculum", "nat", "entrance", "test", "tests",
        "prepare", "preparation", "subject", "subjects", "course", "semester", "semesters",
        "study", "learning", "topics", "books", "psychometric", "critical thinking",
        "81 questions", "negative marking", "crack it", "updated", "skill map",
    ],
    "Campus Life": [
        "campus", "life", "college life", "culture", "sports", "clubs", "events",
        "facilities", "library", "lab", "labs", "infrastructure", "atmosphere",
        "holiday", "holidays", "break", "breaks", "weekend", "safe", "safety",
        "female students", "campus infrastructure", "wi-fi", "cafeteria", "washrooms",
    ],
    "Placements & Career": [
        "placement", "placements", "job", "jobs", "career", "internship", "internships",
        "company", "companies", "hire", "hiring", "salary", "package", "recruiter", "recruiters",
        "interview", "interviews", "guarantee", "guaranteed", "employability",
        "first internship", "mock interviews", "placement support", "graduation",
    ],
    "Rules & Regulations": [
        "rule", "rules", "regulation", "regulations", "policy", "policies",
        "allowed", "allow", "permit", "prohibited", "ban", "attendance", "discipline",
        "leave", "punishment", "complaint", "grievance",
    ],
    "Faculty & Academics": [
        "faculty", "teacher", "teachers", "mentor", "mentors", "professor",
        "academic", "academics", "teaching", "lecture", "lectures", "class", "quality",
        "specialization", "specialisations", "branch", "btech", "b.tech",
        "degree", "degrees", "valid", "government jobs", "higher studies", "abroad",
        "computer science", "cse", "ai", "ml", "data science", "full stack",
        "practical", "theory", "industry", "skill", "skills", "projects", "hackathon",
    ],
    "General": [
        "recognized", "recognition", "nasscom", "government", "worth", "transfer",
        "exactly", "runs", "who runs", "different", "operate", "states", "cities",
        "compare", "comparison", "regular", "private engineering",
    ],
}


def classify_with_keywords(question_text: str) -> str:
    """Score each category by keyword matches; phrases count 2, single words 1. Return best or 'General'."""
    if not question_text or not isinstance(question_text, str):
        return "General"
    text = question_text.lower().strip()
    if not text:
        return "General"
    words = re.findall(r"\w+", text)
    word_set = set(words)
    bigrams = set()
    for i in range(len(words) - 1):
        bigrams.add(f"{words[i]} {words[i+1]}")
    # Build full text for phrase-in-string checks (e.g. "hostel fee")
    best_category = "General"
    best_score = 0
    for category, keywords in CATEGORY_KEYWORDS.items():
        score = 0
        for kw in keywords:
            if " " in kw:
                # Phrase: check bigrams and raw text (weight 2 so phrases win ties)
                if kw in bigrams or kw in text:
                    score += 2
            else:
                if kw in word_set or kw in text:
                    score += 1
        if score > best_score:
            best_score = score
            best_category = category
    return best_category


def classify_with_groq(question_text: str):
    """
    Use Groq (llama-3.1-8b-instant) to classify. Returns (category: str, confidence: float).
    On any failure returns ("General", 0.0). Response must be JSON: {"category": "...", "confidence": 0.0}.
    """
    api_key = getattr(settings, "GROQ_API_KEY", None) or ""
    if not api_key:
        _log("GROQ: skipped — GROQ_API_KEY is empty or not set. Set it in .env to use AI classification.")
        return ("General", 0.0)
    if not question_text or not isinstance(question_text, str):
        _log("GROQ: skipped — no question text.")
        return ("General", 0.0)
    try:
        from groq import Groq
        client = Groq(api_key=api_key)
        prompt = (
            "You are a classifier for student questions about a college (NIAT). "
            "Choose exactly one category from this list: "
            + ", ".join(repr(c) for c in CATEGORIES)
            + ". "
            "Reply with only a JSON object with two keys: \"category\" (exact string from the list) and \"confidence\" (number between 0 and 1). "
            "No other text.\n\nQuestion: "
            + question_text[:1000]
        )
        _log("GROQ: requesting (model=llama-3.1-8b-instant) for question: %s", (question_text[:80] + "..." if len(question_text) > 80 else question_text))
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=60,
        )
        content = (response.choices[0].message.content or "").strip()
        _log("GROQ: raw response: %s", content[:500] if content else "(empty)")
        # Strip markdown code blocks if present
        if content.startswith("```"):
            content = re.sub(r"^```(?:json)?\s*", "", content)
            content = re.sub(r"\s*```\s*$", "", content)
        data = json.loads(content)
        category = (data.get("category") or "General").strip()
        if category not in CATEGORIES:
            _log("GROQ: category %r not in list, using General", category)
            category = "General"
        confidence = float(data.get("confidence", 0.0))
        confidence = max(0.0, min(1.0, confidence))
        _log("GROQ: parsed category=%s confidence=%.2f", category, confidence)
        return (category, confidence)
    except Exception as e:
        _log("GROQ: request failed — %s: %s", type(e).__name__, e)
        logger.exception("Groq classification failed")
        return ("General", 0.0)


class CategoryClassifier:
    """Classify question text with optional Groq LLM and keyword fallback; cache for 7 days."""

    CACHE_PREFIX = "niat_cat_"
    CACHE_TIMEOUT = 7 * 24 * 60 * 60  # 7 days in seconds

    def _cache_key(self, text: str) -> str:
        normalized = (text or "").lower().strip()
        h = hashlib.md5(normalized.encode("utf-8")).hexdigest()
        return self.CACHE_PREFIX + h

    def classify(self, question_text: str) -> dict:
        """
        Return {"category": str, "confidence": float, "source": "llm"|"keyword"}.
        Checks cache first; then Groq if confidence >= 0.35 else keyword fallback; stores in cache.
        """
        if not question_text or not isinstance(question_text, str):
            result = {"category": "General", "confidence": 0.0, "source": "keyword"}
            return result
        key = self._cache_key(question_text)
        cached = cache.get(key)
        if cached is not None:
            _log("classify: cache HIT -> %s (source=%s)", cached.get("category"), cached.get("source"))
            return cached
        category = "General"
        confidence = 0.0
        source = "keyword"
        groq_category, groq_confidence = classify_with_groq(question_text)
        if groq_confidence >= 0.35:
            category = groq_category
            confidence = groq_confidence
            source = "llm"
            _log("classify: using GROQ -> category=%s confidence=%.2f source=llm", category, confidence)
        else:
            category = classify_with_keywords(question_text)
            confidence = 0.0
            source = "keyword"
            _log("classify: using KEYWORD fallback -> category=%s (Groq had confidence=%.2f)", category, groq_confidence)
        result = {"category": category, "confidence": confidence, "source": source}
        cache.set(key, result, self.CACHE_TIMEOUT)
        return result


classifier = CategoryClassifier()
