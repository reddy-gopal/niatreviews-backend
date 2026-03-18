import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from campuses.models import Campus


class Command(BaseCommand):
    help = (
        "Update campus description/google_map_link from a JSON file. "
        "Can update all campuses or a specific campus by slug."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--input",
            type=str,
            default="campuses/data/campus_profile_updates.json",
            help="Path to JSON file (relative to backend/ or absolute path).",
        )
        parser.add_argument(
            "--campus-slug",
            type=str,
            default=None,
            help="If provided, update only this campus slug from the JSON file.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Print what would change without writing to DB.",
        )

    def handle(self, *args, **options):
        input_path = self._resolve_input_path(options["input"])
        campus_slug = options.get("campus_slug")
        dry_run = bool(options.get("dry_run"))

        if not input_path.exists():
            raise CommandError(f"Input file not found: {input_path}")

        try:
            payload = json.loads(input_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise CommandError(f"Invalid JSON in {input_path}: {exc}") from exc

        if not isinstance(payload, list):
            raise CommandError("JSON root must be a list of campus objects.")

        updates_by_slug = {}
        for row in payload:
            if not isinstance(row, dict):
                continue
            slug = (row.get("slug") or "").strip()
            if not slug:
                continue
            updates_by_slug[slug] = row

        if not updates_by_slug:
            raise CommandError("No valid campus rows found. Each row must include 'slug'.")

        target_slugs = [campus_slug] if campus_slug else sorted(updates_by_slug.keys())

        updated_count = 0
        missing_count = 0

        for slug in target_slugs:
            row = updates_by_slug.get(slug)
            if row is None:
                self.stdout.write(self.style.WARNING(f"SKIP {slug}: not present in input file"))
                continue

            campus = Campus.objects.filter(slug=slug).first()
            if not campus:
                missing_count += 1
                self.stdout.write(self.style.WARNING(f"MISS {slug}: campus not found in DB"))
                continue

            new_description = row.get("description")
            new_map_link = row.get("google_map_link")

            changed_fields = []
            if new_description is not None and campus.description != new_description:
                campus.description = new_description
                changed_fields.append("description")
            if new_map_link is not None and campus.google_map_link != new_map_link:
                campus.google_map_link = new_map_link
                changed_fields.append("google_map_link")

            if not changed_fields:
                self.stdout.write(f"NOCHANGE {slug}")
                continue

            if dry_run:
                self.stdout.write(f"DRY-RUN {slug}: would update {', '.join(changed_fields)}")
            else:
                campus.save(update_fields=changed_fields)
                self.stdout.write(self.style.SUCCESS(f"UPDATED {slug}: {', '.join(changed_fields)}"))
            updated_count += 1

        summary = f"Done. Updated: {updated_count}, Missing in DB: {missing_count}"
        if dry_run:
            summary = f"Dry run complete. {summary}"
        self.stdout.write(self.style.SUCCESS(summary))

    def _resolve_input_path(self, value: str) -> Path:
        path = Path(value)
        if path.is_absolute():
            return path
        # manage.py runs from backend/, so relative paths are resolved from cwd.
        return Path.cwd() / path
