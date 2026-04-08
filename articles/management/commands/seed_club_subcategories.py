from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Deprecated: club-directory subcategories are now dynamic from Club table."

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
        self.stdout.write(
            self.style.WARNING(
                "Deprecated command: club-directory options are served dynamically "
                "from active clubs by campus in SubcategoryListView."
            )
        )

