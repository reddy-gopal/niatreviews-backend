from django.db import migrations


def copy_founding_profiles(apps, schema_editor):
    AccountsFoundingProfile = apps.get_model("accounts", "FoundingEditorProfile")
    ProfilesFoundingProfile = apps.get_model("profiles", "FoundingEditorProfile")

    for source in AccountsFoundingProfile.objects.all():
        ProfilesFoundingProfile.objects.get_or_create(
            user_id=source.user_id,
            defaults={
                "linkedin_profile": source.linkedin_profile,
                "campus_id_id": source.campus_id_id,
                "campus_name": source.campus_name,
                "year_joined": source.year_joined,
                "bio": "",
            },
        )


def reverse_copy_founding_profiles(apps, schema_editor):
    ProfilesFoundingProfile = apps.get_model("profiles", "FoundingEditorProfile")
    ProfilesFoundingProfile.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ("profiles", "0001_initial"),
        ("accounts", "0013_user_email_verification_token_user_is_verified"),
    ]

    operations = [
        migrations.RunPython(copy_founding_profiles, reverse_copy_founding_profiles),
    ]
