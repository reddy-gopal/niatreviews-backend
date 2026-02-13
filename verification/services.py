"""
Email services for verification workflow.
"""
from datetime import timedelta

from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone

from .models import MagicLoginToken


def create_magic_login_token(user, expiry_minutes=30):
    """
    Create a single-use magic login token for the user.
    Returns the token UUID (use for building link: /auth/magic?token=<uuid>).
    """
    expires_at = timezone.now() + timedelta(minutes=expiry_minutes)
    ml = MagicLoginToken.objects.create(user=user, expires_at=expires_at)
    return str(ml.token)


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
    login_url = f"https://niatreviews.com/auth/magic?token={magic_token}"

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
    Sent when admin approves a SeniorRegistration and creates user account.
    Uses personal_email and provides login credentials.
    """
    subject = "You're Approved 🎉 Welcome to NIATReviews!"

    # Get username from linked user account
    username = registration.user.username if registration.user else registration.college_email.split('@')[0]

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

Get started now:
👉 Login here: https://niatreviews.com/login

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
