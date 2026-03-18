import json
import logging
import google.generativeai as genai
from django.conf import settings

logger = logging.getLogger(__name__)

# Set to True during loaddata/load_backup so signals do not call Gemini.
_skip_ai_review = False


def skip_ai_review_for_fixture_load(skip=True):
    """Call with skip=True before loaddata; with skip=False after. Used by load_backup."""
    global _skip_ai_review
    _skip_ai_review = bool(skip)


def is_ai_review_skipped():
    """Used by signals to avoid calling Gemini during fixture load."""
    return _skip_ai_review


NIAT_SYSTEM_PROMPT = """
You are a content reviewer for NIAT (NxtWave Institute of Advanced Technologies) —
a specialized engineering education program established in 2023, focused on AI, Machine Learning,
and Data Science. NIAT operates through university partnerships, combining a UGC-recognized
degree with practical industry-ready skills.

NIAT's article platform is written by students for students. Your job is to protect the platform
from harmful or sensitive content while being generous and inclusive toward all genuine student
experiences — positive or negative.

--- WHAT IS ALLOWED (be inclusive) ---
Students can write about virtually anything related to their NIAT life, including:
- Campus life, hostels, food, canteen, nearby restaurants, hangout spots
- Clubs, events, fests, sports, cultural activities
- Placements, internships, coding, projects, career tips
- First 30 days at NIAT, joining experience, onboarding
- Friendships, roommates, daily routines, study tips
- Honest negative experiences (bad food, crowded labs, slow internet) — these are FINE
- Complaints that were resolved quickly — these are GOOD articles
- General student life topics that also happen to apply to other colleges (e.g., "how to stay focused") — ALLOWED as long as it has some NIAT context

--- WHAT MUST BE FLAGGED ---

1. FEE / COST CONTENT (highest priority — check this FIRST):
   - Any mention of fees, pricing, cost, scholarship amounts, or money paid to join NIAT
   - Examples: "I got in for 12 lakhs", "the fee is X per year", "my scholarship covered Y"
   - Even indirect fee disclosures count (e.g., "my parents paid a lot", "it wasn't cheap")
   - Action: set contains_fees = true → status_recommendation = "pending_review"
   - Do NOT reject — the student may have written it innocently. A human will review.

2. UNRESOLVED COMPLAINTS / GRIEVANCES:
   - Articles where the student raised a request or complaint and it was NOT resolved
   - Examples: "I requested a mentor 3 months ago, still no response", "WiFi has been broken for weeks, nobody fixed it", "I raised a ticket but the manager never got back"
   - Contrast: A complaint that WAS resolved quickly ("I raised a WiFi issue and it was fixed in 30 minutes") is a GOOD article — publish it.
   - Action: set unresolved_complaint = true → status_recommendation = "pending_review"
   - Reason: These may damage NIAT's reputation and need a human to decide.

3. OFF-TOPIC CONTENT:
   - Content completely unrelated to NIAT, student life, or campus experience
   - Examples: political opinions, news commentary, product reviews with no NIAT connection
   - Action: set off_topic = true → status_recommendation = "rejected"

4. PROMOTIONAL / SPAM:
   - Articles that read like advertisements, press releases, or recruitment pitches
   - Overly corporate, marketing-speak, or suspiciously positive without any personal voice
   - Action: set promotional = true → status_recommendation = "rejected"

5. LOW QUALITY:
   - Extremely short, incoherent, or meaningless content (e.g., just a few random sentences)
   - Action: set low_quality = true → status_recommendation = "rejected"

--- SCORING GUIDE ---
- confidence_score 0.8–1.0, no flags → "published"
- confidence_score 0.5–0.79 OR contains_fees OR unresolved_complaint → "pending_review"
- confidence_score below 0.5 OR off_topic OR promotional OR low_quality → "rejected"

--- TONE ---
Be fair and generous. Students are writing from lived experience. Do not penalize informal
writing, minor grammar issues, or articles that vent honestly. The goal is to protect the
platform from fee disclosures, unresolved grievances, spam, and truly off-topic content —
not to gatekeep authentic student voices.
"""

REVIEW_PROMPT_TEMPLATE = """
Review this NIAT student article carefully and return a JSON object with this exact structure:

{{
  "confidence_score": <float 0.0–1.0>,
  "brand_alignment": <float 0.0–1.0>,
  "content_quality": <float 0.0–1.0>,
  "tone_score": <float 0.0–1.0>,
  "summary": "<2–3 sentence overall assessment>",
  "status_recommendation": "published" | "pending_review" | "rejected",
  "status_reason": "<1 sentence explaining exactly why you recommend this status>",
  "strengths": ["<strength 1>", "<strength 2>"],
  "concerns": ["<concern 1>", "<concern 2>"],
  "flags": {{
    "contains_fees": <true|false>,
    "unresolved_complaint": <true|false>,
    "off_topic": <true|false>,
    "promotional": <true|false>,
    "low_quality": <true|false>
  }}
}}

--- FLAG PRIORITY (check in this order) ---

STEP 1 — FEE CHECK (most important):
Scan the article for any mention of fees, costs, pricing, scholarship amounts, or money paid.
Even indirect hints like "it wasn't cheap" or "my parents invested a lot" count.
If found → contains_fees = true, status_recommendation = "pending_review"

STEP 2 — UNRESOLVED COMPLAINT CHECK:
Does the article describe a request or complaint that was raised but NOT resolved?
Look for phrases like "still waiting", "no response", "never got back to me", "months later nothing happened".
A resolved complaint ("they fixed it in 30 minutes") is NOT flagged — that's a good article.
If unresolved → unresolved_complaint = true, status_recommendation = "pending_review"

STEP 3 — OFF-TOPIC CHECK:
Is the article completely unrelated to NIAT or student campus life?
If yes → off_topic = true, status_recommendation = "rejected"

STEP 4 — PROMOTIONAL / SPAM CHECK:
Does it read like a press release, ad, or recruitment pitch with no authentic personal voice?
If yes → promotional = true, status_recommendation = "rejected"

STEP 5 — QUALITY CHECK:
Is it extremely short, incoherent, or meaningless?
If yes → low_quality = true, status_recommendation = "rejected"

STEP 6 — PUBLISH:
If none of the above flags are true and confidence_score >= 0.8 → status_recommendation = "published"
If confidence_score is 0.5–0.79 and no flags → status_recommendation = "pending_review"

--- REMINDER ---
Generic student life content is ALLOWED as long as there is some NIAT context.
Honest negative experiences (bad food, slow WiFi, crowded hostel) are ALLOWED and should be published.
Only flag unresolved_complaint if the student explicitly says their issue was NOT resolved.
Do NOT penalise informal language, venting, or minor grammar issues.

You must respond with ONLY a valid JSON object — no markdown, no explanation outside the JSON.

Article Title: {title}
Category: {category}
Campus: {campus_name}
Author: {author_username}

Article Body:
{body}
"""


def review_article_with_gemini(article) -> dict:
    """
    Send article to Gemini for review.
    Returns structured feedback dict.
    Raises exception on API failure — caller handles it.
    """
    try:
        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel(
            model_name="gemini-2.5-pro",
            system_instruction=NIAT_SYSTEM_PROMPT,
        )

        # Strip HTML tags from body for cleaner review
        import re
        clean_body = re.sub(r'<[^>]+>', ' ', article.body or '')
        clean_body = re.sub(r'\s+', ' ', clean_body).strip()
        # Limit to 8000 chars to stay within token limits
        clean_body = clean_body[:8000]

        prompt = REVIEW_PROMPT_TEMPLATE.format(
            title=article.title,
            category=article.category,
            campus_name=article.campus_name or "Unknown",
            author_username=article.author_username or "Unknown",
            body=clean_body,
        )

        response = model.generate_content(prompt)
        raw = response.text.strip()

        # Strip markdown code fences if Gemini wraps in ```json
        if raw.startswith("```"):
            raw = re.sub(r'^```(?:json)?\n?', '', raw)
            raw = re.sub(r'\n?```$', '', raw)

        result = json.loads(raw)

        # Validate required keys exist
        required_keys = [
            "confidence_score", "brand_alignment", "content_quality",
            "tone_score", "summary", "strengths", "concerns",
            "status_recommendation", "status_reason", "flags"
        ]
        for key in required_keys:
            if key not in result:
                raise ValueError(f"Missing key in Gemini response: {key}")

        # Validate flags block has all expected keys
        expected_flags = ["contains_fees", "unresolved_complaint", "off_topic", "promotional", "low_quality"]
        for flag in expected_flags:
            if flag not in result.get("flags", {}):
                result.setdefault("flags", {})[flag] = False

        # Clamp scores between 0 and 1
        for score_key in ["confidence_score", "brand_alignment", "content_quality", "tone_score"]:
            result[score_key] = max(0.0, min(1.0, float(result[score_key])))

        return result

    except json.JSONDecodeError as e:
        logger.error(f"Gemini returned invalid JSON for article {article.id}: {e}")
        raise
    except Exception as e:
        logger.error(f"Gemini review failed for article {article.id}: {e}")
        raise