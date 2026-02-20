# Migration: make SeniorRegistration.personal_email unique

from collections import defaultdict
from django.db import migrations, models


def dedupe_personal_email(apps, schema_editor):
    """
    For duplicate personal_email (case-insensitive), keep the earliest by created_at
    and set others to a unique placeholder so the unique constraint can be applied.
    """
    SeniorRegistration = apps.get_model("verification", "SeniorRegistration")
    by_email = defaultdict(list)
    for r in SeniorRegistration.objects.all().order_by("created_at"):
        key = (r.personal_email or "").strip().lower()
        if key:
            by_email[key].append(r)
    for email_lower, regs in by_email.items():
        for r in regs[1:]:  # keep first, fix the rest
            r.personal_email = f"dup-{r.id}@noreply.niatreviews.local"
            r.save(update_fields=["personal_email"])


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("verification", "0007_rename_verificatio_senior__idx_verificatio_senior__b88b38_idx"),
    ]

    operations = [
        migrations.RunPython(dedupe_personal_email, noop),
        migrations.AlterField(
            model_name="seniorregistration",
            name="personal_email",
            field=models.EmailField(
                db_index=True,
                help_text="Personal email for notifications; must be unique across registrations and users.",
                max_length=254,
                unique=True,
            ),
        ),
    ]
