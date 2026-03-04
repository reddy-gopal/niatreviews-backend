# Remove PhoneVerification model; OTP is sent/verified by MSG91 (no local storage).

from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("verification", "0008_senior_registration_personal_email_unique"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.DeleteModel(name="PhoneVerification"),
    ]
