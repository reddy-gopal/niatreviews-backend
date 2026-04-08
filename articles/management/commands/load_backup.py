"""
Load a backup fixture after flushing the database.

Use this when you want to replace all DB data with the backup. Running
'loaddata <file>' alone can fail with UNIQUE constraint on articles_category.slug
because migration 0002 seeds those categories first. This command flushes then loads
so the fixture is the single source of truth. Handles UTF-16-encoded fixtures by
converting to UTF-8 before load. Skips contenttypes and auth.Permission so Django
recreates them and avoids UNIQUE constraint conflicts when fixture came from another DB.
"""
import json
import tempfile
from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand

from articles.ai_review import skip_ai_review_for_fixture_load

UTF16_LE_BOM = b"\xff\xfe"
UTF16_BE_BOM = b"\xfe\xff"

# Skip these when loading; Django recreates them and fixture PKs often conflict across DBs.
EXCLUDE_MODELS = {"contenttypes.contenttype", "auth.permission"}


class Command(BaseCommand):
    help = "Flush the database and load a backup fixture (default: backup1.json)."

    def add_arguments(self, parser):
        parser.add_argument(
            "fixture",
            nargs="?",
            default="backup1.json",
            help="Fixture file to load (default: backup1.json). Resolved relative to project root.",
        )

    def handle(self, *args, **options):
        fixture = options["fixture"]
        base_dir = Path(settings.BASE_DIR)
        if not fixture.endswith(".json") and not fixture.endswith(".json.gz"):
            fixture = f"{fixture}.json"
        path = Path(fixture) if Path(fixture).is_absolute() else base_dir / fixture

        if not path.exists():
            self.stderr.write(self.style.ERROR(f"Fixture not found: {path}"))
            return

        self.stdout.write("Flushing database...")
        call_command("flush", "--no-input", verbosity=0)
        self.stdout.write(self.style.SUCCESS("Database flushed."))

        # Ensure fixture is UTF-8 and strip contenttypes/auth.Permission to avoid UNIQUE conflicts
        with open(path, "rb") as f:
            raw_head = f.read(4)
        if raw_head.startswith(UTF16_LE_BOM):
            with open(path, "r", encoding="utf-16") as f:
                data = json.load(f)
        elif raw_head.startswith(UTF16_BE_BOM):
            with open(path, "r", encoding="utf-16-be") as f:
                data = json.load(f)
        else:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

        excluded_count = 0
        filtered = []
        for obj in data:
            model = obj.get("model", "").lower()
            if model in EXCLUDE_MODELS:
                excluded_count += 1
                continue
            # Don't load M2M to permissions/groups so we don't reference excluded rows
            if model in ("auth.user", "accounts.user") and "fields" in obj:
                fields = obj["fields"].copy()
                fields.pop("user_permissions", None)
                fields.pop("groups", None)
                obj = {**obj, "fields": fields}
            filtered.append(obj)
        if excluded_count:
            self.stdout.write(
                f"Skipped {excluded_count} contenttypes/permission entries (Django will recreate them)."
            )

        tmp = tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", suffix=".json", delete=False
        )
        json.dump(filtered, tmp, indent=2)
        tmp.close()
        load_path = Path(tmp.name)
        tmp_path = load_path

        self.stdout.write(f"Loading fixture: {path}...")
        skip_ai_review_for_fixture_load(True)
        try:
            call_command("loaddata", str(load_path), verbosity=1)
            self.stdout.write(self.style.SUCCESS("Backup loaded successfully."))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Load failed: {e}"))
            raise
        finally:
            skip_ai_review_for_fixture_load(False)
            if tmp_path is not None and tmp_path.exists():
                tmp_path.unlink()
