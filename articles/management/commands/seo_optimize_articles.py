import json
import time
import os
import re
import csv
from django.core.management.base import BaseCommand
from articles.models import Article
import anthropic


# ─────────────────────────────────────────────
# LOAD KEYWORDS FROM CSV
# ─────────────────────────────────────────────

KEYWORD_FILE_PATH = "NIAT Insider _ Keyword research  - Copy of Queries.csv"


def load_keywords_from_csv():
    keywords = set()

    try:
        with open(KEYWORD_FILE_PATH, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            for row in reader:
                kw = (
                    row.get('query') or
                    row.get('keyword') or
                    row.get('Query') or
                    list(row.values())[0]
                )

                if kw:
                    kw = kw.strip().lower()
                    if len(kw) > 2:
                        keywords.add(kw)

    except Exception as e:
        print(f"❌ Error loading keywords: {e}")

    return list(keywords)


ALL_KEYWORDS = load_keywords_from_csv()


# ─────────────────────────────────────────────
# SMART KEYWORD SELECTION (NO LIMIT)
# ─────────────────────────────────────────────

def get_keywords_for_article(article) -> list:
    campus = (article.campus_name or '').lower()
    category = (article.category or '').lower()
    title = (article.title or '').lower()

    scored = []

    for kw in ALL_KEYWORDS:
        score = 0

        if campus and campus in kw:
            score += 5

        if category and category.replace('-', ' ') in kw:
            score += 3

        if any(word in kw for word in title.split()):
            score += 2

        if "niat" in kw:
            score += 2

        if len(kw.split()) >= 3:
            score += 1

        if score > 0:
            scored.append((kw, score))

    scored.sort(key=lambda x: x[1], reverse=True)

    # 🔥 NO LIMIT — send everything relevant
    return [kw for kw, _ in scored]


# ─────────────────────────────────────────────
# COMMAND
# ─────────────────────────────────────────────

class Command(BaseCommand):
    help = 'SEO generation using FULL article + FULL keyword set (no limits)'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true')
        parser.add_argument('--article-id', type=str)
        parser.add_argument('--overwrite', action='store_true')
        parser.add_argument('--limit', type=int, default=100)

    def handle(self, *args, **options):
        api_key = os.environ.get('ANTHROPIC_API_KEY')

        if not api_key:
            self.stdout.write(self.style.ERROR('ANTHROPIC_API_KEY missing'))
            return

        client = anthropic.Anthropic(api_key=api_key)

        if options['article_id']:
            articles = Article.objects.filter(
                id=options['article_id'],
                status='published',
            )
        else:
            articles = Article.objects.filter(
                status='published',
                is_global_guide=False,
                campus_id__isnull=False,
            )

        total = articles.count()
        success = skipped = errors = processed_count = 0
        limit = options['limit']

        self.stdout.write(f'Found {total} articles\n')

        for article in articles:

            if processed_count >= limit:
                break

            if not options['overwrite']:
                if (
                    article.meta_title and
                    article.meta_description and
                    article.meta_keywords
                ):
                    skipped += 1
                    continue

            try:
                keywords = get_keywords_for_article(article)
                result = self.generate_seo_with_retry(client, article, keywords)

                if options['dry_run']:
                    self.stdout.write(f"""
TITLE: {result['title']}
SLUG: {result['slug']}
META TITLE: {result['meta_title']}
META DESC: {result['meta_description']}
KEYWORDS: {", ".join(result['meta_keywords'])}
""")
                else:
                    article.title = result['title']
                    article.slug = result['slug']
                    article.meta_title = result['meta_title']
                    article.meta_description = result['meta_description']
                    article.meta_keywords = result['meta_keywords']

                    if result['first_paragraph'] and article.body:
                        article.body = self.replace_first_paragraph(
                            article.body,
                            result['first_paragraph']
                        )

                    article.save()

                success += 1
                processed_count += 1
                time.sleep(0.5)

            except Exception as e:
                self.stdout.write(self.style.ERROR(str(e)))
                errors += 1

        self.stdout.write(self.style.SUCCESS(
            f"\nDone → {success} success | {skipped} skipped | {errors} errors"
        ))


    # ─────────────────────────────────────────────
    # RETRY
    # ─────────────────────────────────────────────

    def generate_seo_with_retry(self, client, article, keywords, max_retries=3):
        delay = 5

        for attempt in range(max_retries):
            try:
                return self.generate_seo(client, article, keywords)

            except anthropic.RateLimitError:
                time.sleep(delay)
                delay *= 2

            except Exception:
                if attempt == max_retries - 1:
                    raise
                time.sleep(2)


    # ─────────────────────────────────────────────
    # CORE SEO (NO LIMITS)
    # ─────────────────────────────────────────────

    def generate_seo(self, client, article, keywords):

        # 🔥 FULL BODY (no truncation)
        body_content = ''
        if article.body:
            body_content = re.sub(r'<[^>]+>', '', article.body)
            body_content = re.sub(r'\s+', ' ', body_content).strip()

        keywords_str = '\n'.join(f'- {kw}' for kw in keywords)

        system_prompt = """You are an expert SEO strategist.
Return ONLY valid JSON. No explanation."""

        user_prompt = f"""
Optimise this article for maximum Google ranking.

TITLE: {article.title}
CAMPUS: {article.campus_name}
CATEGORY: {article.category}

FULL ARTICLE:
{body_content}

ALL AVAILABLE KEYWORDS:
{keywords_str}

INSTRUCTIONS:

- Identify primary, secondary, and long-tail keywords
- Use semantic SEO (variations, questions, intent)
- Focus on ranking for multiple queries
- Use natural language (no stuffing)
- Extract insights from FULL article content

RETURN JSON:

{{
  "title": "",
  "slug": "",
  "meta_title": "",
  "meta_description": "",
  "meta_keywords": [],
  "first_paragraph": ""
}}
"""

        message = client.messages.create(
            model='claude-haiku-4-5-20251001',
            max_tokens=1500,  # response size only (NOT input limit)
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )

        raw = message.content[0].text.strip()

        if '```' in raw:
            raw = raw.split('```')[-1]

        result = json.loads(raw)

        return result


    # ─────────────────────────────────────────────
    # HELPERS
    # ─────────────────────────────────────────────

    def clean_slug(self, slug):
        slug = slug.lower()
        slug = re.sub(r'[^a-z0-9-]', '-', slug)
        slug = re.sub(r'-+', '-', slug)
        return slug.strip('-')


    def replace_first_paragraph(self, body, new_para):
        return re.sub(
            r'<p[^>]*>.*?</p>',
            f'<p>{new_para}</p>',
            body,
            count=1,
            flags=re.DOTALL
        )