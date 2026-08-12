"""
Intelligence Signals
Auto-create profiles when users are created
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import StudentIntelligenceProfile

User = get_user_model()


@receiver(post_save, sender=User)
def create_intelligence_profile(sender, instance, created, **kwargs):
    """
    Automatically create an intelligence profile when a user is created.
    """
    if created:
        StudentIntelligenceProfile.objects.create(user=instance)
