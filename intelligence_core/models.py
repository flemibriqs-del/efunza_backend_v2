import uuid
from django.conf import settings
from django.db import models
from django.utils import timezone

try:
    # use JSONField compatible with Django versions
    from django.db.models import JSONField
except Exception:
    from django.contrib.postgres.fields import JSONField


class StudentIntelligenceProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='intelligence_profile')
    overall_mastery = models.FloatField(default=0.0)
    skills = JSONField(default=list, blank=True)
    weaknesses = JSONField(default=list, blank=True)
    goals = JSONField(default=list, blank=True)
    history_summary = JSONField(default=list, blank=True)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"StudentIntelligenceProfile(user={self.user_id})"


class Evidence(models.Model):
    """Structured evidence created from activities (ItemAttempt, StudentScore, SimulatorLog, RAG interactions, etc.)"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile = models.ForeignKey(StudentIntelligenceProfile, on_delete=models.CASCADE, related_name='evidence')
    source_type = models.CharField(max_length=64)  # e.g., item_attempt, student_score, simulator, rag_interaction
    source_id = models.CharField(max_length=255, null=True, blank=True)
    activity_type = models.CharField(max_length=128, null=True, blank=True)
    payload = JSONField(default=dict, blank=True)
    confidence = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Evidence(id={self.id}, profile={self.profile_id}, source={self.source_type})"


class MasteryRecord(models.Model):
    profile = models.ForeignKey(StudentIntelligenceProfile, on_delete=models.CASCADE, related_name='masteries')
    concept_id = models.CharField(max_length=255)  # domain:slug e.g., maritime:man-overboard
    mastery_score = models.FloatField(default=0.0)
    uncertainty = models.FloatField(default=1.0)
    evidence_refs = JSONField(default=list, blank=True)  # list of evidence UUIDs
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = (('profile', 'concept_id'),)
        ordering = ['-last_updated']

    def __str__(self):
        return f"MasteryRecord(profile={self.profile_id}, concept={self.concept_id}, score={self.mastery_score})"
