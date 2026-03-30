import json
import re
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.utils.text import slugify

from campuses.models import Campus
from articles.models import Club, ClubCampus


def _norm(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (value or "").strip().lower())


class Command(BaseCommand):
    help = "Import/update clubs and campus chapters from backend/data.json"

    def add_arguments(self, parser):
        parser.add_argument(
            "--path",
            type=str,
            default="data.json",
            help="Path to source JSON file (default: backend/data.json).",
        )

    def handle(self, *args, **options):
        json_path = Path(options["path"])
        if not json_path.is_absolute():
            json_path = Path.cwd() / json_path
        if not json_path.exists():
            raise CommandError(f"File not found: {json_path}")

        try:
            payload = json.loads(json_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise CommandError(f"Invalid JSON in {json_path}: {exc}") from exc

        if not isinstance(payload, list):
            raise CommandError("Expected top-level JSON array of campuses.")

        campuses = list(Campus.objects.all())
        by_short_name = {_norm(c.short_name or ""): c for c in campuses if (c.short_name or "").strip()}
        by_name = {_norm(c.name): c for c in campuses}

        created_clubs = 0
        updated_clubs = 0
        linked_chapters = 0
        updated_chapters = 0
        skipped_campuses = []

        for campus_item in payload:
            campus_key = (campus_item or {}).get("campus")
            clubs = (campus_item or {}).get("clubs") or []
            if not isinstance(clubs, list):
                continue

            match_key = _norm(str(campus_key or ""))
            campus = by_short_name.get(match_key) or by_name.get(match_key)
            if campus is None:
                skipped_campuses.append(str(campus_key))
                continue

            for item in clubs:
                club_name = str((item or {}).get("club_name") or "").strip()
                if not club_name:
                    continue
                objective = str((item or {}).get("objective") or "").strip()
                president = str((item or {}).get("president") or "").strip()
                instagram = str((item or {}).get("instagram") or "").strip()
                linkedin = str((item or {}).get("linkedin") or "").strip()
                slug = slugify(club_name)[:120] or f"club-{campus.id.hex[:8]}"

                club, club_created = Club.objects.get_or_create(
                    slug=slug,
                    defaults={
                        "name": club_name,
                        "objective": objective,
                        "is_active": True,
                    },
                )
                if club_created:
                    created_clubs += 1
                else:
                    changed = False
                    if club.name != club_name:
                        club.name = club_name
                        changed = True
                    if objective and club.objective != objective:
                        club.objective = objective
                        changed = True
                    if changed:
                        club.save(update_fields=["name", "objective", "updated_at"])
                        updated_clubs += 1

                chapter, chapter_created = ClubCampus.objects.get_or_create(
                    club=club,
                    campus=campus,
                    defaults={
                        "president_name": president,
                        "instagram": instagram,
                        "linkedin": linkedin,
                        "is_active": True,
                    },
                )
                if chapter_created:
                    linked_chapters += 1
                else:
                    changed = False
                    if president and chapter.president_name != president:
                        chapter.president_name = president
                        changed = True
                    if instagram and chapter.instagram != instagram:
                        chapter.instagram = instagram
                        changed = True
                    if linkedin and chapter.linkedin != linkedin:
                        chapter.linkedin = linkedin
                        changed = True
                    if changed:
                        chapter.save(update_fields=["president_name", "instagram", "linkedin", "updated_at"])
                        updated_chapters += 1

        self.stdout.write(self.style.SUCCESS("Club import completed."))
        self.stdout.write(
            f"Created clubs: {created_clubs}, Updated clubs: {updated_clubs}, "
            f"Created chapters: {linked_chapters}, Updated chapters: {updated_chapters}"
        )
        if skipped_campuses:
            self.stdout.write(self.style.WARNING(f"Skipped unmatched campuses: {', '.join(sorted(set(skipped_campuses)))}"))

