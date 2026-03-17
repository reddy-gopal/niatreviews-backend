import json
import logging
import google.generativeai as genai
from django.conf import settings

logger = logging.getLogger(__name__)

NIAT_SYSTEM_PROMPT = """
You are a strict content reviewer for NIAT (NxtWave Institute of Advanced Technologies) — 
a specialized engineering education program established in 2023, focused on AI, Machine Learning, 
and Data Science. NIAT operates through university partnerships, combining a UGC-recognized 
degree with practical industry-ready skills.

NIAT's article platform is written by students for students. Good articles are:
- Practical and helpful (campus life, food, clubs, placements, internships, coding)
- First-person, peer-to-peer, friendly and authentic in tone
- Specific to NIAT campus experience
- Honest and conversational — not corporate or press-release-like

An article should be REJECTED or scored low if it:
- Mentions fees, pricing, or fee structures in any form
- Contains content unrelated to NIAT or student campus life
- Sounds plagiarized, overly formal, or like a press release
- Is promotional or spam-like
- Has political content
- Is generic enough to apply to any college (no NIAT-specific value)

You must respond with ONLY a valid JSON object — no markdown, no explanation outside the JSON.
"""
REVIEW_PROMPT_TEMPLATE = """
Review this NIAT student article and return a JSON object with this exact structure:

{{
  "confidence_score": <float between 0.0 and 1.0>,
  "brand_alignment": <float between 0.0 and 1.0>,
  "content_quality": <float between 0.0 and 1.0>,
  "tone_score": <float between 0.0 and 1.0>,
  "summary": "<2-3 sentence overall assessment>",
  "status_recommendation": "published" | "pending_review" | "rejected",
  "status_reason": "<1 sentence explaining exactly why you recommend this status>",
  "strengths": ["<strength 1>", "<strength 2>"],
  "concerns": ["<concern 1>", "<concern 2>"],
  "flags": {{
    "contains_fees": <true|false>,
    "off_topic": <true|false>,
    "promotional": <true|false>,
    "low_quality": <true|false>
  }}
}}

Scoring guide:
- confidence_score 0.8–1.0 + no flags → status_recommendation: "published"
- confidence_score 0.5–0.79 OR minor concerns → status_recommendation: "pending_review"  
- confidence_score below 0.5 OR any true flag → status_recommendation: "rejected"

status_recommendation must match one of the Article status values exactly:
"published", "pending_review", or "rejected"

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
            model_name="gemini-2.5-flash",
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

        # Validate required keys exist (match prompt: status_recommendation, status_reason)
        required_keys = [
            "confidence_score", "brand_alignment", "content_quality",
            "tone_score", "summary", "strengths", "concerns",
            "status_recommendation", "status_reason", "flags"
        ]
        for key in required_keys:
            if key not in result:
                raise ValueError(f"Missing key in Gemini response: {key}")

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