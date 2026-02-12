"""
SeniorProfile: keep User.is_verified_senior in sync when approved/rejected.
PhoneVerification: when verified_at is set and user is set, update User.phone_number and User.phone_verified.
Import in verification.apps.Ready to connect.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import SeniorProfile, PhoneVerification


@receiver(post_save, sender=SeniorProfile)
def sync_verified_senior_flag(sender, instance, **kwargs):
    """Set user.is_verified_senior True only when status is 'approved'."""
    user = instance.user
    new_value = instance.status == "approved"
    if user.is_verified_senior != new_value:
        user.is_verified_senior = new_value
        user.save(update_fields=["is_verified_senior"])


@receiver(post_save, sender=PhoneVerification)
def sync_phone_verified_on_user(sender, instance, **kwargs):
    """When OTP is verified (verified_at set) and user is linked, set User.phone_number and User.phone_verified."""
    if instance.verified_at is None or instance.user_id is None:
        return
    user = instance.user
    if user.phone_number != instance.phone_number or not user.phone_verified:
        user.phone_number = (instance.phone_number or "").strip() or None
        user.phone_verified = True
        user.save(update_fields=["phone_number", "phone_verified"])
