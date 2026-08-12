"""
Intelligence App Configuration
"""

from django.apps import AppConfig


class IntelligenceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'intelligence'
    verbose_name = 'Intelligence Engine'
    
    def ready(self):
        """
        Import signals when the app is ready.
        """
        import intelligence.signals
