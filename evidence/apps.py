from django.apps import AppConfig


class EvidenceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'evidence'
    verbose_name = 'Evidence & Competency'
    
    def ready(self):
        # Import any signal handlers if needed
        pass
