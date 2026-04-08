import re
from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand, CommandError

from articles.models import Article


class Command(BaseCommand):
    help = (
        "Upload local media/article/images files to Cloudflare R2 via default_storage. "
        "Optionally rewrite existing Article URLs to R2 URLs."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--prefix",
            default="article/images",
            help="Path prefix under MEDIA_ROOT to migrate (default: article/images).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Only print actions without uploading or modifying DB.",
        )
        parser.add_argument(
            "--rewrite-urls",
            action="store_true",
            help="Rewrite Article.body / cover_image / images URLs from local media to R2 URLs.",
        )

    def handle(self, *args, **options):
        if not getattr(settings, "USE_CLOUDFLARE_R2", False):
            raise CommandError(
                "USE_CLOUDFLARE_R2 is not enabled. Enable R2 storage before running migration."
            )

        prefix = options["prefix"].strip("/").replace("\\", "/")
        dry_run = options["dry_run"]
        rewrite_urls = options["rewrite_urls"]

        source_root = Path(settings.MEDIA_ROOT) / prefix
        if not source_root.exists():
            raise CommandError(f"Source directory does not exist: {source_root}")

        uploaded = 0
        skipped = 0
        failed = 0
        migrated_paths = []

        files = [p for p in source_root.rglob("*") if p.is_file()]
        self.stdout.write(self.style.NOTICE(f"Found {len(files)} files under {source_root}"))

        for file_path in files:
            rel_path = str(file_path.relative_to(settings.MEDIA_ROOT)).replace("\\", "/")
            try:
                if default_storage.exists(rel_path):
                    skipped += 1
                    migrated_paths.append(rel_path)
                    continue
                if dry_run:
                    uploaded += 1
                    migrated_paths.append(rel_path)
                    continue
                with file_path.open("rb") as f:
                    default_storage.save(rel_path, File(f))
                uploaded += 1
                migrated_paths.append(rel_path)
            except Exception as exc:
                failed += 1
                self.stderr.write(self.style.ERROR(f"Failed: {rel_path} ({exc})"))

        rewritten = 0
        if rewrite_urls:
            media_url = getattr(settings, "LOCAL_MEDIA_URL", "/media/").rstrip("/")
            replacements = {}
            path_to_remote = {}
            rel_paths_for_rewrite = set(migrated_paths)

            # Include image paths currently referenced in article fields, even if
            # the local source file is no longer present on disk.
            marker = f"{media_url}/"
            for article in Article.objects.all().iterator():
                values = [article.body or "", article.cover_image or ""]
                images = article.images or []
                if isinstance(images, list):
                    values.extend([img for img in images if isinstance(img, str)])
                for value in values:
                    if marker not in value:
                        continue
                    parts = value.split(marker)
                    for segment in parts[1:]:
                        rel = segment.split('"')[0].split("'")[0].split(")")[0].split("<")[0].strip()
                        if rel:
                            rel_paths_for_rewrite.add(rel)

            for rel_path in rel_paths_for_rewrite:
                if not default_storage.exists(rel_path):
                    continue
                remote_url = default_storage.url(rel_path)
                if remote_url.startswith("/"):
                    # Should not happen for R2 public URLs, but keep fallback.
                    remote_url = f"{settings.R2_PUBLIC_BASE_URL.rstrip('/')}{remote_url}"
                path_to_remote[rel_path] = remote_url
                local_path_url = f"{media_url}/{rel_path}"
                local_candidates = {
                    local_path_url,
                    f"http://127.0.0.1:8000{local_path_url}",
                    f"http://localhost:8000{local_path_url}",
                    f"https://127.0.0.1:8000{local_path_url}",
                    f"https://localhost:8000{local_path_url}",
                }
                for old in local_candidates:
                    replacements[old] = remote_url

            for article in Article.objects.all().iterator():
                changed = False

                body = article.body or ""
                for old, new in replacements.items():
                    if old in body:
                        body = body.replace(old, new)
                        changed = True
                for rel_path, remote_url in path_to_remote.items():
                    media_rel = f"{media_url}/{rel_path}"
                    if media_rel in body:
                        body = body.replace(media_rel, remote_url)
                        changed = True
                    pattern = rf"https?://[^\"'\s)]+{re.escape(media_rel)}"
                    updated_body = re.sub(pattern, remote_url, body)
                    if updated_body != body:
                        body = updated_body
                        changed = True
                if body != article.body:
                    article.body = body

                cover = article.cover_image or ""
                if cover in replacements:
                    article.cover_image = replacements[cover]
                    changed = True
                else:
                    for rel_path, remote_url in path_to_remote.items():
                        media_rel = f"{media_url}/{rel_path}"
                        if media_rel in cover or re.search(
                            rf"https?://[^\"'\s)]+{re.escape(media_rel)}", cover
                        ):
                            article.cover_image = remote_url
                            changed = True
                            break

                images = article.images or []
                if isinstance(images, list):
                    new_images = []
                    for img in images:
                        replaced = replacements.get(img)
                        if replaced:
                            new_images.append(replaced)
                            continue
                        resolved = img
                        for rel_path, remote_url in path_to_remote.items():
                            media_rel = f"{media_url}/{rel_path}"
                            if media_rel in (img or "") or re.search(
                                rf"https?://[^\"'\s)]+{re.escape(media_rel)}", img or ""
                            ):
                                resolved = remote_url
                                break
                        new_images.append(resolved)
                    if new_images != images:
                        article.images = new_images
                        changed = True

                if changed and not dry_run:
                    article.save(update_fields=["body", "cover_image", "images", "updated_at"])
                if changed:
                    rewritten += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Article image migration done. uploaded={uploaded} skipped={skipped} failed={failed}"
            )
        )
        if rewrite_urls:
            self.stdout.write(self.style.SUCCESS(f"Articles with URL rewrites: {rewritten}"))
