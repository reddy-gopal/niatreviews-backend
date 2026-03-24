"""
humanize_articles.py
────────────────────────────────────────────────────────────────────
Django management command: Transcript → Human Student Blog

What it does:
  1. Finds AI-generated articles (ai_generated=True, status='published')
  2. Strips ALL video / YouTube language from the raw body
  3. Rewrites as a PURE FIRST-PERSON student blog — written BY the student,
     not ABOUT the student. No "she shares", no "he explains". Just "I".
  4. Picks ONLY relevant keywords from your CSV sheet
  5. Saves fully complete (never truncated) SEO fields
  6. Marks article as ai_generated=False when done

Usage:
  python manage.py humanize_articles                     # all pending
  python manage.py humanize_articles --limit 5           # 5 at a time
  python manage.py humanize_articles --article-id <uuid> # single article
  python manage.py humanize_articles --dry-run           # preview only
  python manage.py humanize_articles --overwrite         # redo humanized

Model fields written:
  title, slug, excerpt, body,
  meta_title, meta_description, meta_keywords, ai_generated
"""

import csv
import json
import os
import re
import time

from django.core.management.base import BaseCommand
from articles.models import Article
import anthropic


# ─────────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────────

KEYWORD_FILE_PATH = "NIAT Insider _ Keyword research  - Copy of Queries.csv"

TOPIC_RESTRICTED_KEYWORDS = {
    "fee", "fees", "fee structure", "tuition", "scholarship",
    "syllabus", "curriculum", "course structure",
    "placement", "placements", "package", "salary", "lpa",
    "admission", "entrance", "eligibility", "cutoff",
    "ranking", "rank", "accreditation", "naac",
}

# CSS classes — add these to your global stylesheet
HTML_CLASSES = {
    "article_wrap"   : "ni-article",
    "intro_para"     : "ni-intro",
    "section_heading": "ni-h2",
    "body_para"      : "ni-para",
    "highlight_box"  : "ni-highlight",
    "list_wrap"      : "ni-list",
    "list_item"      : "ni-list-item",
    "quote_block"    : "ni-quote",
    "author_note"    : "ni-author-note",
}

# All HTML entities / smart quotes that must be plain UTF-8 in output
ENCODING_FIXES = {
    # Smart quotes and apostrophes
    '\u2018'   : "'",   # left single quotation mark
    '\u2019'   : "'",   # right single quotation mark  ← the it's problem
    '\u201c'   : '"',   # left double quotation mark
    '\u201d'   : '"',   # right double quotation mark
    '\u2026'   : '...', # ellipsis
    '\u2013'   : '-',   # en dash
    '\u2014'   : '--',  # em dash
    # HTML entities
    '&#x27;'   : "'",
    '&#39;'    : "'",
    '&quot;'   : '"',
    '&amp;'    : '&',
    '&nbsp;'   : ' ',
    '&apos;'   : "'",
    # Mojibake artifacts
    'â€™'      : "'",
    'â€œ'      : '"',
    'â€\x9d'   : '"',
    'â€¦'      : '...',
    'Ã¢â‚¬â„¢': "'",
    'Ã¢â‚¬Å"' : '"',
    'Ã¢â‚¬'   : '"',
    'Æ'        : "'",
}


# ─────────────────────────────────────────────────────────────────
# KEYWORD LOADER
# ─────────────────────────────────────────────────────────────────

def load_all_keywords() -> list[str]:
    if not os.path.exists(KEYWORD_FILE_PATH):
        return []
    keywords = []
    with open(KEYWORD_FILE_PATH, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            kw = (
                row.get('query') or row.get('keyword') or
                row.get('Keyword') or row.get('Query') or
                (list(row.values())[0] if row else '')
            )
            if kw and kw.strip():
                keywords.append(kw.strip().lower())
    return keywords


def pick_relevant_keywords(
    all_keywords: list[str],
    article_body: str,
    campus_name: str,
    category: str,
    max_keywords: int = 60,
) -> list[str]:
    """
    Return only keywords that genuinely match this article's topic + campus.
    Never injects fee/placement/admission keywords into a lifestyle article.
    """
    body_lower   = article_body.lower()
    campus_lower = (campus_name or '').lower()

    signal_map = {
        'hostel'      : ['hostel', 'dorm', 'room', 'pg', 'accommodation'],
        'food'        : ['food', 'mess', 'canteen', 'cafeteria', 'eat', 'lunch', 'dinner'],
        'club'        : ['club', 'society', 'team', 'committee', 'activity', 'activities'],
        'hackathon'   : ['hackathon', 'buildathon', 'project', 'coding', 'hack'],
        'exam'        : ['exam', 'test', 'assessment', 'marks', 'grade', 'study'],
        'workshop'    : ['workshop', 'seminar', 'session', 'training'],
        'campus life' : ['campus', 'college', 'day', 'routine', 'schedule', 'life'],
        'fest'        : ['fest', 'festival', 'event', 'cultural', 'sports', 'celebration'],
        'placement'   : ['placement', 'job', 'offer', 'package', 'company', 'hired'],
        'fee'         : ['fee', 'fees', 'cost', 'expense', 'scholarship', 'tuition'],
        'admission'   : ['admission', 'apply', 'entrance', 'join', 'enroll'],
    }

    topic_signals = {
        signal
        for signal, triggers in signal_map.items()
        if any(t in body_lower for t in triggers)
    }

    relevant = []
    for kw in all_keywords:
        kw_lower = kw.lower()

        if kw_lower in (
            'niat', 'niat college', 'nxtwave institute of advanced technologies',
            'niat nxtwave', 'niat india', 'what is niat',
        ):
            relevant.append(kw)
            continue

        is_restricted = any(r in kw_lower for r in TOPIC_RESTRICTED_KEYWORDS)

        if campus_lower and campus_lower in kw_lower:
            if is_restricted:
                if (
                    ('fee'       in topic_signals and any(r in kw_lower for r in ('fee', 'fees', 'tuition'))) or
                    ('placement' in topic_signals and any(r in kw_lower for r in ('placement', 'package'))) or
                    ('admission' in topic_signals and any(r in kw_lower for r in ('admission', 'entrance')))
                ):
                    relevant.append(kw)
            else:
                relevant.append(kw)
            continue

        if not is_restricted:
            for signal in topic_signals:
                if signal in kw_lower or any(t in kw_lower for t in signal_map.get(signal, [])):
                    relevant.append(kw)
                    break
            else:
                if any(x in kw_lower for x in ('niat', 'campus', 'student', 'first year', 'btech', 'b.tech')):
                    relevant.append(kw)

    seen, unique = set(), []
    for kw in relevant:
        if kw not in seen:
            seen.add(kw)
            unique.append(kw)
    return unique[:max_keywords]


# ─────────────────────────────────────────────────────────────────
# MANAGEMENT COMMAND
# ─────────────────────────────────────────────────────────────────

class Command(BaseCommand):
    help = "Rewrite AI-generated transcript articles into human student blog posts"

    def add_arguments(self, parser):
        parser.add_argument('--dry-run',    action='store_true',
                            help='Preview output without saving')
        parser.add_argument('--overwrite',  action='store_true',
                            help='Re-process already-humanized articles')
        parser.add_argument('--article-id', type=str,
                            help='Process a single article by UUID')
        parser.add_argument('--limit',      type=int, default=50,
                            help='Max articles per run (default: 50)')

    def handle(self, *args, **options):
        api_key = os.environ.get('ANTHROPIC_API_KEY')
        if not api_key:
            self.stdout.write(self.style.ERROR(
                'ANTHROPIC_API_KEY not set.\n'
                'Add to .env:  ANTHROPIC_API_KEY=sk-ant-...\n'
            ))
            return

        all_keywords = load_all_keywords()
        if all_keywords:
            self.stdout.write(f'{len(all_keywords)} keywords loaded from CSV\n')
        else:
            self.stdout.write(self.style.WARNING(
                f'Keyword CSV not found at: {KEYWORD_FILE_PATH}\n'
                f'Continuing without CSV keywords.\n'
            ))

        client = anthropic.Anthropic(api_key=api_key)

        if options['article_id']:
            articles = Article.objects.filter(id=options['article_id'], status='published')
        elif options['overwrite']:
            articles = Article.objects.filter(status='published')
        else:
            articles = Article.objects.filter(ai_generated=True, status='published')

        total   = articles.count()
        limit   = options['limit']
        success = skipped = errors = 0

        self.stdout.write(f'Found {total} articles | limit: {limit}\n')
        self.stdout.write('─' * 65 + '\n')

        for article in articles:
            if success >= limit:
                self.stdout.write(self.style.WARNING(
                    f'\nLimit of {limit} reached. Run again to continue.\n'
                ))
                break

            self.stdout.write(
                f'\n[{success + 1}] {article.title[:70]}\n'
                f'    author   : {article.author_username}\n'
                f'    campus   : {article.campus_name or "Unknown"}\n'
                f'    category : {article.category}\n'
            )

            try:
                clean_body = self._strip_html(article.body or '')

                relevant_kws = pick_relevant_keywords(
                    all_keywords,
                    clean_body,
                    article.campus_name or '',
                    article.category or '',
                )
                self.stdout.write(f'    keywords matched: {len(relevant_kws)}\n')

                result = self.rewrite_with_retry(client, article, clean_body, relevant_kws)

                if options['dry_run']:
                    self._print_dry_run(result)
                else:
                    article.title            = result['title']
                    article.slug             = self._clean_slug(result['slug'])
                    article.excerpt          = result['excerpt']
                    article.body             = result['body']
                    article.meta_title       = result['meta_title']
                    article.meta_description = result['meta_description']
                    article.meta_keywords    = result['meta_keywords']
                    article.ai_generated     = False

                    article.save(update_fields=[
                        'title', 'slug', 'excerpt', 'body',
                        'meta_title', 'meta_description', 'meta_keywords',
                        'ai_generated', 'updated_at',
                    ])
                    self.stdout.write(self.style.SUCCESS(
                        f'    SAVED  slug: {article.slug}\n'
                    ))

                success += 1
                time.sleep(0.5)

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'    ERROR: {e}\n'))
                errors += 1

        self.stdout.write('\n' + '─' * 65 + '\n')
        self.stdout.write(self.style.SUCCESS(
            f'Done.  Processed: {success} | Skipped: {skipped} | Errors: {errors}\n'
        ))

    def _print_dry_run(self, result: dict):
        self.stdout.write(f"""
┌─ DRY RUN ──────────────────────────────────────────────────────
│ title            : {result['title']}
│ slug             : {result['slug']}
│ meta_title       : {result['meta_title']}
│ meta_description : {result['meta_description']}
│ excerpt          : {result['excerpt']}
│ keywords ({len(result['meta_keywords'])})     : {', '.join(result['meta_keywords'])}
│
│ body preview (600 chars):
│ {result['body'][:600].replace(chr(10), chr(10) + '│ ')}
└────────────────────────────────────────────────────────────────
""")

    # ─────────────────────────────────────────────
    # Retry wrapper
    # ─────────────────────────────────────────────

    def rewrite_with_retry(self, client, article, clean_body, relevant_kws, max_retries=3):
        delay = 5
        for attempt in range(1, max_retries + 1):
            try:
                return self.rewrite_article(client, article, clean_body, relevant_kws)
            except anthropic.RateLimitError:
                if attempt < max_retries:
                    self.stdout.write(f'    Rate limited. Waiting {delay}s...\n')
                    time.sleep(delay)
                    delay *= 2
                else:
                    raise
            except anthropic.APIStatusError as e:
                if e.status_code == 529 and attempt < max_retries:
                    self.stdout.write(f'    API overloaded. Retrying in {delay}s...\n')
                    time.sleep(delay)
                    delay *= 2
                else:
                    raise
            except json.JSONDecodeError:
                if attempt < max_retries:
                    self.stdout.write(f'    Bad JSON. Retrying (attempt {attempt})...\n')
                    time.sleep(3)
                else:
                    raise Exception('Claude returned invalid JSON after all retries.')

    # ─────────────────────────────────────────────
    # Core rewrite
    # ─────────────────────────────────────────────

    def rewrite_article(self, client, article: Article, clean_body: str, relevant_kws: list) -> dict:
        campus          = article.campus_name or 'NIAT'
        category        = article.category or 'campus-life'
        author_username = article.author_username or 'a NIAT student'

        title_lower = (article.title or '').lower()
        body_lower  = clean_body.lower()

        if any(w in body_lower or w in title_lower for w in ['review', 'honest', 'experience', 'feedback']):
            intent = 'HONEST STUDENT REVIEW'
        elif any(w in body_lower or w in title_lower for w in ['hackathon', 'buildathon', 'competition']):
            intent = 'TECH EVENT / HACKATHON'
        elif any(w in body_lower or w in title_lower for w in ['club', 'workshop', 'seminar', 'activity']):
            intent = 'CAMPUS ACTIVITY / CLUB'
        elif any(w in body_lower or w in title_lower for w in ['fest', 'festival', 'cultural', 'event']):
            intent = 'CAMPUS FEST / EVENT'
        elif any(w in body_lower or w in title_lower for w in ['food', 'mess', 'hostel']):
            intent = 'CAMPUS LIFE / HOSTEL'
        elif any(w in body_lower or w in title_lower for w in ['exam', 'study', 'marks']):
            intent = 'ACADEMIC EXPERIENCE'
        else:
            intent = 'CAMPUS LIFESTYLE'

        keywords_str = '\n'.join(f'  - {k}' for k in relevant_kws) or '  - niat\n  - niat college'
        c = HTML_CLASSES

        system_prompt = """\
You are a B.Tech student at NIAT (NxtWave Institute of Advanced Technologies).
You are writing a personal blog post on NIAT Insider — a student community platform.

YOU ARE THE STUDENT. You are writing about YOUR OWN life and experiences.
This is YOUR story, written in YOUR voice.
Write like a teenager or a recent school graduate (10th/12th standard level).

CRITICAL — VOICE RULES:
- Write ENTIRELY in first person: I, me, my, we, our
- NEVER write "she shares", "he explains", "the student says", "according to her"
- NEVER describe yourself from the outside — you are living it, not observing it
- Write like you are typing a WhatsApp message to a college friend, but slightly more structured
- Use real student phrases: "Honestly,", "Not gonna lie,", "To be real,", "My take:",
  "If you're curious,", "Here's the thing —", "Okay so,", "Lowkey,", "No cap,"

ABSOLUTE RULES — NEVER break these:
1. ZERO video references — never write: "in this video", "watch", "subscribe",
   "hey guys", "comment below", "like and share", "channel", "thumbnail",
   "footage", "screen", "clip", "reel", "viewers", "audience"
2. ZERO third-person narration — the moment you write "she" or "he" about the author, you have failed
3. ZERO AI filler — never write: "delve", "it's worth noting", "in conclusion",
   "furthermore", "moreover", "it is important to", "comprehensive", "this article aims to"
4. Use only straight apostrophes: write it's, don't, I'm, I've — NOT smart quotes
5. Output ONLY valid JSON — no markdown fences, no explanation outside the JSON object"""

        user_prompt = f"""\
TASK: Rewrite the content below as a personal blog post written BY the student themselves.

WHO IS WRITING THIS:
  username : {author_username}
  campus   : {campus}
  category : {category}
  intent   : {intent}

The author is writing about their own real experiences at NIAT {campus}.
They are NOT summarizing a video. They are NOT describing someone else.
They are typing out their own story the way they lived it.

SOURCE CONTENT (the raw story — extract the real experiences, ignore any video structure):
\"\"\"
{clean_body[:4500]}
\"\"\"

KEYWORDS (pick only what genuinely fits this article — never force irrelevant ones):
{keywords_str}

━━━ SEO FIELD RULES ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

title
  - 55-70 characters. Count before writing.
  - Start with: NIAT {campus}
  - Specific and intriguing, never generic
  - Written as if the student titled their own blog post
  - Good: "NIAT {campus}: What My First B.Tech Year Actually Looks Like"
  - Bad:  "A Student Shares Her Experience at NIAT"

slug
  - 4-6 lowercase words, hyphens only, no stop words
  - Good: niat-{campus.lower().replace(' ', '-')}-first-year-routine
  - Bad:  a-student-shares-her-experience-at-niat-college

meta_title
  - HARD MAX 60 characters total including "| NIAT Insider"
  - Format: [topic] | NIAT Insider
  - Written from student perspective
  - Good (54 chars): "My NIAT {campus[:15]} Daily Routine | NIAT Insider"

meta_description
  - HARD MAX 148 characters
  - Must be a COMPLETE sentence — never cut mid-word or mid-sentence
  - Written in first person or as a direct hook to the student reader
  - First 8 words must answer what someone would search for
  - End with: "Read my story." / "Here is what happened." / "This is what I learned."
  - No quote marks inside the description
  - Good: "My real first-year routine at NIAT {campus[:12]} — from chaotic mornings to late coding sessions. Here is what a B.Tech day actually looks like."

excerpt
  - 2-3 complete sentences. HARD MAX 300 characters.
  - Written in first person — YOUR voice, YOUR story
  - Hook that makes another NIAT student want to read
  - Must end at a complete sentence — never cut mid-word
  - Good: "My mornings at NIAT Ajeenkya start with bad decisions and chia seeds. Here is the full unfiltered breakdown of what a B.Tech first year day actually feels like."

meta_keywords
  - Pick 6-8 from the keyword list above
  - Only keywords that genuinely match this article
  - All lowercase

━━━ HTML BODY RULES ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Write 500-900 words of clean semantic HTML.
CSS classes below are already in the frontend stylesheet — just apply them correctly.

REQUIRED STRUCTURE:

<article class="{c['article_wrap']}">

  <!-- OPENING PARAGRAPH — SEO + hook -->
  <!-- This paragraph must rank on Google AND make the reader stay -->
  <p class="{c['intro_para']}">
    - 2-3 sentences
    - Must include "NIAT {campus}" + the article topic
    - Do NOT start with "I" — open with a scene, moment, or feeling
    - Then pull the reader in with your honest take
    - Good: "Mornings at NIAT {campus} never go according to plan. Mine start
      with chia seeds I don't actually like, earrings I spend way too long
      picking, and a coding session I am already late for."
    - Bad: "I am a student at NIAT Ajeenkya DY Patil University."
  </p>

  <!-- SECTION 1 — tell your story -->
  <h2 class="{c['section_heading']}">Catchy, specific section title — not generic</h2>
  <p class="{c['body_para']}">
    - 3-5 sentences
    - Specific real details from the source content
    - Your feelings, reactions, honest opinions
    - Student phrases welcome
  </p>

  <!-- HIGHLIGHT BOX — one key insight, tip, or honest moment -->
  <div class="{c['highlight_box']}">
    <p>One punchy line. Your real take on something. 1-2 sentences max.</p>
  </div>

  <!-- SECTION 2 -->
  <h2 class="{c['section_heading']}">Another specific section title</h2>
  <p class="{c['body_para']}">3-5 sentences in your voice.</p>

  <!-- LIST — use when you have 3 or more specific items -->
  <ul class="{c['list_wrap']}">
    <li class="{c['list_item']}">specific real item</li>
    <li class="{c['list_item']}">specific real item</li>
    <li class="{c['list_item']}">specific real item</li>
  </ul>

  <!-- SECTION 3+ — add more as needed -->
  <h2 class="{c['section_heading']}">Third section title</h2>
  <p class="{c['body_para']}">3-5 sentences.</p>

  <!-- OPTIONAL: quote from a friend or your own thought -->
  <blockquote class="{c['quote_block']}">
    A real quote or thought that captures the moment.
  </blockquote>

  <!-- CLOSING — your sign-off, what you learned or want freshers to know -->
  <!-- Do NOT write "In conclusion" or "To summarize" -->
  <p class="{c['author_note']}">
    1-2 sentences. Personal and honest. What would you tell a fresher joining NIAT?
  </p>

</article>

BODY QUALITY RULES:
- EVERY sentence uses "I", "my", "me", "we", "our" — always first person
- NEVER: "she", "he", "the student", "the author", "one might", "students often"
- <h2> titles: SPECIFIC — not "Introduction" / "My Experience" / "Overview"
  Good: "The 2AM Panic That Became My Study Method"
  Bad:  "My Study Experience at NIAT"
- Every <p>: 3-5 sentences. No one-liners. No walls of text.
- Use only straight apostrophes in text: it's, don't, I'm, I've, can't
- At least 3 <h2> sections
- At least 1 <div class="{c['highlight_box']}">
- At least 1 <ul> with real specific items

━━━ OUTPUT ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Return ONLY this JSON. No markdown. No fences. No text outside the object.
Use straight apostrophes (') not smart quotes in all text values.

{{
  "title": "55-70 char title",
  "slug": "4-6-word-slug",
  "excerpt": "2-3 sentence first-person hook under 300 chars.",
  "meta_title": "Short topic | NIAT Insider (max 60 chars)",
  "meta_description": "Complete first-person sentence under 148 chars ending with CTA.",
  "meta_keywords": ["kw1", "kw2", "kw3", "kw4", "kw5", "kw6"],
  "body": "<article class=\\"{c['article_wrap']}\\">...full HTML...</article>"
}}"""

        message = client.messages.create(
            model='claude-haiku-4-5-20251001',
            max_tokens=5000,
            system=system_prompt,
            messages=[{'role': 'user', 'content': user_prompt}],
        )

        raw = message.content[0].text.strip()
        raw = self._extract_json(raw)
        result = json.loads(raw)

        # Post-process
        result['title']            = self._safe_field(result.get('title', ''),            70,  500)
        result['slug']             = self._clean_slug(result.get('slug', ''))
        result['excerpt']          = self._safe_field(result.get('excerpt', ''),          300, 1000)
        result['meta_title']       = self._safe_meta_title(result.get('meta_title', ''))
        result['meta_description'] = self._safe_meta_description(result.get('meta_description', ''))
        result['meta_keywords']    = [k.lower().strip() for k in result.get('meta_keywords', [])[:8]]
        result['body']             = self._clean_body(result.get('body', ''))

        # Fix encoding on all text fields
        for field in ('title', 'excerpt', 'meta_title', 'meta_description'):
            result[field] = self._fix_encoding(result[field])

        return result

    # ─────────────────────────────────────────────
    # Helpers
    # ─────────────────────────────────────────────

    def _strip_html(self, html: str) -> str:
        """Remove HTML tags and normalise whitespace."""
        text = re.sub(r'<[^>]+>', ' ', html)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def _fix_encoding(self, text: str) -> str:
        """Replace all smart quotes, HTML entities, and mojibake with plain UTF-8."""
        for bad, good in ENCODING_FIXES.items():
            text = text.replace(bad, good)
        # Final pass: remove any remaining HTML entities
        text = re.sub(r'&#\d+;', "'", text)
        text = re.sub(r'&[a-zA-Z]+;', ' ', text)
        return text

    def _safe_field(self, text: str, max_chars: int, hard_limit: int) -> str:
        """
        Trim to max_chars at a sentence boundary then word boundary.
        Never exceeds hard_limit (the actual DB field limit).
        """
        text = text.strip()
        if len(text) <= max_chars:
            return text[:hard_limit]
        cut = text[:max_chars]
        for sep in ('. ', '! ', '? '):
            idx = cut.rfind(sep)
            if idx > max_chars // 2:
                return cut[:idx + 1].strip()
        return cut.rsplit(' ', 1)[0]

    def _safe_meta_title(self, meta_title: str) -> str:
        """
        Rebuild meta_title cleanly:
        base (max 45 chars at word boundary) + ' | NIAT Insider' = max 60 chars
        CharField(max_length=255) — no DB truncation risk.
        """
        suffix   = ' | NIAT Insider'
        max_base = 60 - len(suffix)  # 45 chars
        base = re.sub(r'\s*\|.*$', '', meta_title).strip()
        if len(base) > max_base:
            base = base[:max_base].rsplit(' ', 1)[0]
        return base + suffix

    def _safe_meta_description(self, desc: str) -> str:
        """
        Keep under 148 chars, ending at a complete sentence.
        TextField — no DB truncation risk, but Google truncates in SERP at ~155.
        """
        desc = self._fix_encoding(desc.strip())
        # Remove any double quotes (break JSON if returned inside a JSON string)
        desc = desc.replace('"', "'")

        if len(desc) <= 148:
            return desc
        cut = desc[:148]
        for sep in ('. ', '! ', '? '):
            idx = cut.rfind(sep)
            if idx > 80:
                return cut[:idx + 1].strip()
        return cut.rsplit(' ', 1)[0].rstrip('.,;:') + '.'

    def _extract_json(self, raw: str) -> str:
        """Robustly extract a JSON object from Claude's response."""
        if '```' in raw:
            parts = raw.split('```')
            for part in parts:
                part = part.strip()
                if part.startswith('json'):
                    part = part[4:].strip()
                if part.strip().startswith('{'):
                    return part.strip()
        start = raw.find('{')
        end   = raw.rfind('}')
        if start != -1 and end != -1:
            return raw[start:end + 1]
        return raw

    def _clean_slug(self, slug: str) -> str:
        """Sanitize slug — SlugField(max_length=600), kept ≤80 for clean URLs."""
        slug = slug.lower().strip()
        slug = re.sub(r'[^a-z0-9\-]', '-', slug)
        slug = re.sub(r'-+', '-', slug)
        return slug.strip('-')[:80]

    def _clean_body(self, body: str) -> str:
        """
        Final scrub of the HTML body:
        1. Fix all encoding issues (smart quotes, mojibake, HTML entities)
        2. Remove any lingering video / YouTube phrases
        3. Remove third-person narration slippage
        4. Remove AI writing tells
        5. Normalise whitespace
        """
        # Fix encoding first — before regex so patterns match correctly
        body = self._fix_encoding(body)

        # ── Video language ──
        video_patterns = [
            r'in\s+this\s+video[,.]?',
            r'watch\s+(this|the)\s+video',
            r'hey\s+guys[,!]?',
            r'welcome\s+back(\s+to\s+(my|the|our)\s+channel)?[,!]?',
            r"don'?t\s+forget\s+to\s+(like|subscribe|comment|share)",
            r'(hit|click)\s+(the\s+)?(like|subscribe|bell)\s+button',
            r'comment\s+(down\s+)?below',
            r'subscribe\s+(to|for)\s+\w+',
            r'(check|watch)\s+(this|the|my)\s+(video|channel|playlist)',
            r'(see|watch)\s+you\s+(in\s+the\s+next|next\s+time)',
            r'(thanks|thank\s+you)\s+for\s+watching',
            r"in\s+today'?s\s+video",
            r'as\s+(I|we)\s+(show|showed|mentioned)\s+in\s+(the|this)\s+video',
            r'(on|in)\s+screen',
            r'(the\s+|this\s+)?thumbnail',
            r'this\s+(clip|footage|reel)',
            r'(my|our|the)\s+channel',
            r'you\s+guys',
            r'drop\s+a\s+(like|comment)',
        ]
        for p in video_patterns:
            body = re.sub(p, '', body, flags=re.IGNORECASE)

        # ── Third-person narration slippage ──
        # These patterns catch cases where Claude accidentally slips into
        # "she says", "he explains", "the student describes"
        third_person_patterns = [
            r'\bshe\s+(shares|says|explains|describes|mentions|notes|adds|reveals|admits|recalls)\b',
            r'\bhe\s+(shares|says|explains|describes|mentions|notes|adds|reveals|admits|recalls)\b',
            r'\bthe\s+student\s+\w+s\b',
            r'\bthe\s+author\s+\w+s\b',
            r'\baccording\s+to\s+her\b',
            r'\baccording\s+to\s+him\b',
        ]
        for p in third_person_patterns:
            body = re.sub(p, '', body, flags=re.IGNORECASE)

        # ── AI writing tells ──
        ai_patterns = [
            r'\bdelving?\b',
            r"\bit'?s\s+worth\s+noting\b",
            r'\bin\s+conclusion\b',
            r'\bfurthermore\b',
            r'\bmoreover\b',
            r'\bit\s+is\s+important\s+to\b',
            r'\bthis\s+article\s+aims\s+to\b',
            r'\bcomprehensive(ly)?\b',
            r'\bin\s+summary\b',
            r'\bto\s+summarize\b',
            r'\bto\s+conclude\b',
            r'\bas\s+mentioned\s+earlier\b',
            r'\boverall\b',
        ]
        for p in ai_patterns:
            body = re.sub(p, '', body, flags=re.IGNORECASE)

        # ── Whitespace cleanup ──
        body = re.sub(r'\n{3,}', '\n\n', body)
        body = re.sub(r'[ \t]{2,}', ' ', body)
        # Clean up empty tags left after pattern removal
        body = re.sub(r'<(p|h2|div|li)[^>]*>\s*</\1>', '', body)

        return body.strip()