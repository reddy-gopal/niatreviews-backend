"""
Email services for verification workflow.
"""
import builtins
import uuid as uuid_module
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.utils import timezone

from .models import MagicLoginToken, SeniorProfile

User = get_user_model()


def create_user_and_senior_profile_for_registration(registration):
    """
    Create a User and SeniorProfile for an approved SeniorRegistration and link them.
    Call this when registration.status is "approved" and registration.user_id is None.
    Returns the created User, or None if already linked or creation failed.
    """
    if registration.user_id is not None:
        return None
    username = registration.college_email.split("@")[0].strip()
    if User.objects.filter(username=username).exists():
        return None
    try:
        password = uuid_module.uuid4().hex
        user = User.objects.create_user(
            username=username,
            email=registration.personal_email,
            first_name=registration.call_name,
            password=password,
            role="senior",
        )
        user.set_unusable_password()
        user.save(update_fields=["password"])
        proof = (
            f"Registration Details:\n"
            f"College: {registration.partner_college}\n"
            f"Year: {registration.graduation_year}\n"
            f"Branch: {registration.branch}\n\n"
            f"Why Join: {registration.why_join}\n\n"
            f"Best Experience: {registration.best_experience}\n\n"
            f"Advice: {registration.advice_to_juniors}\n\n"
            f"Skills: {registration.skills_gained}"
        )
        SeniorProfile.objects.create(
            user=user,
            proof_summary=proof,
            status="approved",
        )
        SeniorRegistration = registration.__class__
        SeniorRegistration.objects.filter(pk=registration.pk).update(user=user)
        return user
    except Exception:
        return None


def create_magic_login_token(user, expiry_minutes=30):
    """
    Create a single-use magic login token for the user.
    Returns the token UUID (use for building link: /auth/magic?token=<uuid>).
    """
    expires_at = timezone.now() + timedelta(minutes=expiry_minutes)
    ml = MagicLoginToken.objects.create(user=user, expires_at=expires_at)
    return builtins.str(ml.token)


def send_senior_received_email(user):
    """
    Sent immediately after senior submits verification request.
    Confirms receipt and sets expectations.
    """
    subject = "We Received Your NIAT Senior Registration 🎓"

    message = f"""Hi {user.first_name or user.username},

Thank you for applying to become a Verified NIAT Senior on NIATReviews!

We have successfully received your verification request and our team is currently reviewing your submission.

What happens next?
• Our admin team will review your credentials
• You'll receive an email notification once your profile is approved
• This typically takes 1-2 business days

We appreciate your patience and look forward to having you as part of our verified senior community!

Best regards,
The NIATReviews Team

---
Need help? Reply to this email or contact us at support@niatreviews.com
"""

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )


def send_senior_approved_email(user):
    """
    Sent when admin approves the senior profile.
    Congratulates and provides next steps. Includes magic login link (30 min).
    """
    subject = "You're Approved 🎉 Welcome to NIATReviews!"
    magic_token = create_magic_login_token(user)
    base_url = getattr(settings, "MAIN_APP_URL", "https://niatreviews.com").rstrip("/")
    login_url = f"{base_url}/auth/magic?token={magic_token}"

    message = f"""Hi {user.first_name or user.username},

Congratulations! 🎉

Your NIAT Senior verification has been approved! You are now a Verified Senior on NIATReviews.

What you can do now:
• Answer questions from prospective students
• Share your NIAT experience and insights
• Help guide the next generation of NIAT students
• Build your reputation as a trusted mentor

Get started now (this link expires in 30 minutes):
👉 Click to log in: {login_url}

Your verified senior badge will be visible on all your posts and comments, helping students identify authentic advice from real NIAT seniors.

Thank you for joining our community of verified mentors!

Welcome aboard,
The NIATReviews Team

---
Questions? Reply to this email or visit our help center at niatreviews.com/help
"""

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )



def send_senior_registration_received_email(registration):
    """
    Sent immediately after senior submits detailed registration from seniors-frontend.
    Uses personal_email since user account doesn't exist yet.
    """
    subject = "We Received Your NIAT Senior Registration 🎓"

    message = f"""Hi {registration.call_name},

Thank you for applying to become a Verified NIAT Senior on NIATReviews!

We have successfully received your registration with the following details:
• Name: {registration.full_name}
• College: {registration.partner_college}
• Branch: {registration.branch}
• Graduation Year: {registration.graduation_year}

What happens next?
• Our admin team will review your credentials and ID card
• We'll verify your college email and phone number
• You'll receive an email notification once your profile is approved
• This typically takes 1-2 business days

We appreciate your patience and look forward to having you as part of our verified senior community!

Best regards,
The NIATReviews Team

---
Need help? Reply to this email or contact us at support@niatreviews.com
"""

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [registration.personal_email],
        fail_silently=False,
    )


def send_senior_registration_approved_email(registration):
    """
    Sent when admin approves a SeniorRegistration (via signal).
    When registration.user is set, includes a one-time magic login link so the senior
    can sign in, set their password, and complete onboarding.
    """
    subject = "You're Approved 🎉 Welcome to NIATReviews!"
    username = registration.user.username if registration.user else registration.college_email.split('@')[0]

    # One-time magic login link when we have a linked user (admin has created the account)
    login_line = "👉 Login here: https://niatreviews.com/login"
    if registration.user_id:
        magic_token = create_magic_login_token(registration.user)
        base_url = getattr(settings, "MAIN_APP_URL", "https://niatreviews.com").rstrip("/")
        login_url = f"{base_url}/auth/magic?token={magic_token}"
        login_line = f"Get started now (this link expires in 30 minutes):\n👉 Sign in with one click: {login_url}\n\nAfter signing in you’ll set a password and answer a few NIAT review questions, then you can start answering questions from prospective students."

    message = f"""Hi {registration.call_name},

Congratulations! 🎉

Your NIAT Senior registration has been approved! We've created your account and you are now a Verified Senior on NIATReviews.

Your Account Details:
• Username: {username}
• Email: {registration.personal_email}
• College: {registration.partner_college}
• Branch: {registration.branch}

What you can do now:
• Answer questions from prospective students
• Share your NIAT experience and insights
• Help guide the next generation of NIAT students
• Build your reputation as a trusted mentor

{login_line}

Your verified senior badge will be visible on all your posts and comments, helping students identify authentic advice from real NIAT seniors.

Thank you for joining our community of verified mentors!

Welcome aboard,
The NIATReviews Team

---
Questions? Reply to this email or visit our help center at niatreviews.com/help
"""

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [registration.personal_email],
        fail_silently=False,
    )


def send_senior_registration_rejected_email(registration):
    """
    Sent when admin rejects a SeniorRegistration.
    Uses personal_email and provides feedback.
    """
    subject = "NIAT Senior Registration Update"

    message = f"""Hi {registration.call_name},

Thank you for your interest in becoming a Verified NIAT Senior on NIATReviews.

After reviewing your application, we are unable to approve your registration at this time.

Common reasons for rejection:
• Incomplete or unclear ID card verification
• Information that doesn't match our records
• Missing required documentation

What you can do:
• Review your application details
• Ensure all information is accurate and complete
• Resubmit your application with updated information

We encourage you to apply again once you've addressed any potential issues.

If you have questions about this decision, please reply to this email and our team will be happy to provide more specific feedback.

Best regards,
The NIATReviews Team

---
Need help? Reply to this email or contact us at support@niatreviews.com
"""

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [registration.personal_email],
        fail_silently=False,
    )
