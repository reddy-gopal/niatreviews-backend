from django.db.models.signals import pre_save
from django.dispatch import receiver

from .models import User


@receiver(pre_save, sender=User)
def validate_user_role(sender, instance, **kwargs):
    User.validate_role_value(instance.role)
