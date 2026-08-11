from django.apps import AppConfig


class IntelligenceCoreConfig(AppConfig):
    default_auto_field = 'django.db.models.AutoField'
    name = 'intelligence_core'

    def ready(self):
        # import signal handlers
        try:
            from . import signals  # noqa: F401
        except Exception:
            # In some CI or import situations this may fail; it's okay to defer
            pass
