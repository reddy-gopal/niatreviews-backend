from .models import AuditLog


def get_client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "") if request else ""
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR") if request else None


def log_action(actor, action, entity, target_user=None, metadata=None, request=None):
    AuditLog.objects.create(
        actor=actor,
        action=action,
        entity_type=entity.__class__.__name__,
        entity_id=str(entity.pk),
        target_user=target_user,
        metadata=metadata or {},
        ip_address=get_client_ip(request) if request else None,
    )
