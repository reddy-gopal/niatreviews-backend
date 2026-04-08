import os

try:
    from celery import Celery
except ImportError:  # pragma: no cover
    Celery = None

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings.local")

if Celery is None:  # pragma: no cover
    class _CeleryStub:
        def task(self, *args, **kwargs):
            def decorator(func):
                return func

            return decorator

        def autodiscover_tasks(self, *args, **kwargs):
            return None

    app = _CeleryStub()
else:
    app = Celery("backend")
    app.config_from_object("django.conf:settings", namespace="CELERY")
    app.autodiscover_tasks()
