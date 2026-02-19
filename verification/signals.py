"""
Verification signals.
Sync user flags and send emails on status changes.
"""
from django.db.models import F
from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from .models import SeniorFollow, SeniorProfile, PhoneVerification, SeniorRegistration
from .services import (
    create_user_and_senior_profile_for_registration,
    send_senior_approved_email,
    send_senior_registration_approved_email,
    send_senior_registration_rejected_email,
)


@receiver(pre_save, sender=SeniorProfile)
def track_old_status(sender, instance, **kwargs):
    """
    Store old status before saving so we can detect changes.
    This runs before the instance is saved to the database.
    """
    if not instance.pk:
        # New instance - no old status
        instance._old_status = None
    else:
        # Existing instance - fetch old status from database
        try:
            old_instance = SeniorProfile.objects.get(pk=instance.pk)
            instance._old_status = old_instance.status
        except SeniorProfile.DoesNotExist:
            instance._old_status = None


@receiver(post_save, sender=SeniorProfile)
def handle_senior_profile_changes(sender, instance, created, **kwargs):
    """
    Handle SeniorProfile changes:
    1. Sync user.is_verified_senior flag
    2. Send approval email when status becomes approved (only once)
    """
    user = instance.user

    # 1. Sync is_verified_senior flag
    new_value = instance.status == "approved"
    if user.is_verified_senior != new_value:
        user.is_verified_senior = new_value
        user.save(update_fields=["is_verified_senior"])

    # 2. Send approval email ONLY when status transitions to approved
    # Check: not a new creation, old status was not approved, new status is approved
    if (
        not created
        and hasattr(instance, "_old_status")
        and instance._old_status != "approved"
        and instance.status == "approved"
    ):
        try:
            send_senior_approved_email(user)
        except Exception as e:
            # Log error but don't fail the save
            print(f"Failed to send senior approval email: {e}")


@receiver(pre_save, sender=SeniorRegistration)
def track_old_registration_status(sender, instance, **kwargs):
    """
    Store old status before saving so we can detect changes.
    This runs before the instance is saved to the database.
    """
    if not instance.pk:
        # New instance - no old status
        instance._old_status = None
    else:
        # Existing instance - fetch old status from database
        try:
            old_instance = SeniorRegistration.objects.get(pk=instance.pk)
            instance._old_status = old_instance.status
        except SeniorRegistration.DoesNotExist:
            instance._old_status = None


@receiver(post_save, sender=SeniorRegistration)
def handle_senior_registration_changes(sender, instance, created, **kwargs):
    """
    When status changes to "approved": create User + SeniorProfile if not yet linked, then send email.
    When status changes to "rejected": send rejection email.
    """
    if created:
        return
    if not hasattr(instance, "_old_status") or instance._old_status == instance.status:
        return

    try:
        if instance._old_status != "approved" and instance.status == "approved":
            # Create user and profile when first approved (no user linked yet)
            if instance.user_id is None:
                create_user_and_senior_profile_for_registration(instance)
                instance.refresh_from_db()
            if instance.user_id is not None:
                send_senior_registration_approved_email(instance)
        elif instance._old_status != "rejected" and instance.status == "rejected":
            send_senior_registration_rejected_email(instance)
    except Exception as e:
        import logging
        logging.getLogger(__name__).exception("Senior registration signal failed: %s", e)


@receiver(post_save, sender=PhoneVerification)
def sync_phone_verified_flag(sender, instance, created, **kwargs):
    """
    When PhoneVerification is verified, sync user.phone_verified and user.phone_number.
    """
    if instance.verified_at and instance.user:
        user = instance.user

        # Update phone_verified flag
        if not user.phone_verified:
            user.phone_verified = True
            user.phone_number = instance.phone_number
            user.save(update_fields=["phone_verified", "phone_number"])


@receiver(post_save, sender=SeniorFollow)
def senior_follow_created(sender, instance, created, **kwargs):
    """Increment senior's follower_count when a follow is created."""
    if not created:
        return
    SeniorProfile.objects.filter(user_id=instance.senior_id).update(
        follower_count=F("follower_count") + 1
    )


@receiver(post_delete, sender=SeniorFollow)
def senior_follow_deleted(sender, instance, **kwargs):
    """Decrement senior's follower_count when a follow is removed."""
    SeniorProfile.objects.filter(user_id=instance.senior_id).update(
        follower_count=F("follower_count") - 1
    )
