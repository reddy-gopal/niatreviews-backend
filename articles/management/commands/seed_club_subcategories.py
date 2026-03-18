from django.core.management.base import BaseCommand, CommandError

from articles.models import Category, Club, Subcategory
from campuses.models import Campus


class Command(BaseCommand):
    help = "Seed campus-specific club-directory subcategories from active clubs."

    def add_arguments(self, parser):
        parser.add_argument(
            "--campus",
            required=True,
            help="Campus slug to seed (e.g. niat-hyderabad).",
        )

    def handle(self, *args, **options):
        campus_slug = (options.get("campus") or "").strip()
        if not campus_slug:
            raise CommandError("Please provide --campus <slug>.")

        try:
            campus = Campus.objects.get(slug=campus_slug)
        except Campus.DoesNotExist as exc:
            raise CommandError(f"Campus not found: {campus_slug}") from exc

        try:
            category = Category.objects.get(slug="club-directory")
        except Category.DoesNotExist as exc:
            raise CommandError("Category 'club-directory' not found.") from exc

        clubs = (
            Club.objects.filter(campus=campus, is_active=True)
            .order_by("name")
            .only("slug", "name")
        )

        created_count = 0
        updated_count = 0
        skipped_count = 0

        order = 0
        for club in clubs:
            defaults = {
                "label": club.name,
                "requires_other": False,
                "display_order": order,
            }
            existing = Subcategory.objects.filter(
                category=category,
                campus=campus,
                slug=club.slug,
            ).first()
            obj, created = Subcategory.objects.update_or_create(
                category=category,
                campus=campus,
                slug=club.slug,
                defaults=defaults,
            )
            if created:
                created_count += 1
            else:
                changed = existing is not None and any(
                    getattr(existing, field) != value for field, value in defaults.items()
                )
                if changed:
                    updated_count += 1
                else:
                    skipped_count += 1
            order += 1

        others_defaults = {
            "label": "Others",
            "requires_other": True,
            "display_order": order,
        }
        existing_others = Subcategory.objects.filter(
            category=category,
            campus=campus,
            slug="others",
        ).first()
        others_obj, others_created = Subcategory.objects.update_or_create(
            category=category,
            campus=campus,
            slug="others",
            defaults=others_defaults,
        )
        if others_created:
            created_count += 1
        else:
            changed = existing_others is not None and any(
                getattr(existing_others, field) != value
                for field, value in others_defaults.items()
            )
            if changed:
                updated_count += 1
            else:
                skipped_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded club subcategories for campus={campus.slug}: "
                f"created={created_count}, updated={updated_count}, skipped={skipped_count}"
            )
        )

