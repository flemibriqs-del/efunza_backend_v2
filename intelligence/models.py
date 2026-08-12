# intelligence/models.py

from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal
import uuid
import json

User = get_user_model()

class StudentIntelligenceProfile(models.Model):
    """
    Central learner model - the single source of truth for all learning data.
    """
    # Core identifiers
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='intelligence_profile')
    
    # Learning goals & preferences
    learning_goals = models.JSONField(default=list, help_text="List of learning goals with priorities")
    preferred_learning_styles = models.JSONField(default=list)  # visual, auditory, kinesthetic, etc.
    career_interests = models.JSONField(default=list)  # List of career paths
    current_learning_path = models.CharField(max_length=100, blank=True)
    
    # Mastery & competency tracking (dynamic, updated by Mastery Engine)
    concept_mastery = models.JSONField(default=dict)  # {concept_id: mastery_score (0-1)}
    topic_mastery = models.JSONField(default=dict)    # {topic_id: mastery_score}
    subject_mastery = models.JSONField(default=dict)  # {subject_id: mastery_score}
    
    # Skills & competencies (evidence-based)
    skills = models.JSONField(default=list)  # [{skill_id: str, proficiency: float, evidence: list}]
    competencies = models.JSONField(default=list)  # [{competency_id: str, level: str, evidence: list}]
    
    # Weaknesses & gaps (identified by Mastery Engine)
    weaknesses = models.JSONField(default=list)  # [{concept_id: str, gap_score: float, priority: int}]
    
    # Learning history summary
    total_attempts = models.PositiveIntegerField(default=0)
    total_correct = models.PositiveIntegerField(default=0)
    average_score = models.FloatField(default=0.0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    study_streak_days = models.PositiveIntegerField(default=0)
    last_activity_date = models.DateTimeField(null=True, blank=True)
    
    # Engagement metrics
    engagement_score = models.FloatField(default=0.5, validators=[MinValueValidator(0), MaxValueValidator(1)])
    consistency_score = models.FloatField(default=0.5, validators=[MinValueValidator(0), MaxValueValidator(1)])
    curiosity_score = models.FloatField(default=0.5, validators=[MinValueValidator(0), MaxValueValidator(1)])
    
    # Advanced metrics
    knowledge_growth_rate = models.FloatField(default=0.0)  # Rate of knowledge acquisition
    predicted_learning_speed = models.FloatField(default=0.0)  # Personalized speed prediction
    
    # Career readiness
    career_readiness_level = models.CharField(max_length=20, default='beginner')
    recommended_career_paths = models.JSONField(default=list)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    version = models.PositiveIntegerField(default=1)  # For tracking profile evolution
    
    class Meta:
        indexes = [
            models.Index(fields=['user', 'updated_at']),
            models.Index(fields=['career_readiness_level']),
        ]
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"Intelligence Profile - {self.user.email}"
    
    def get_mastery_for_concept(self, concept_id):
        """Get mastery level for a specific concept."""
        return self.concept_mastery.get(str(concept_id), 0.0)
    
    def get_weakness_priority(self, concept_id):
        """Get the priority of a weakness (higher = more urgent)."""
        for weakness in self.weaknesses:
            if weakness.get('concept_id') == str(concept_id):
                return weakness.get('priority', 0)
        return 0
    
    def update_engagement_score(self, activity_type, performance):
        """
        Dynamic engagement score update based on activity type and performance.
        """
        # Weighted update based on activity type
        weights = {
            'quiz': 0.3,
            'simulation': 0.4,
            'practical': 0.5,
            'learning': 0.2,
            'assessment': 0.35,
        }
        
        weight = weights.get(activity_type, 0.3)
        performance_factor = performance / 100.0  # Normalize performance
        
        # Exponential moving average for smoother updates
        alpha = 0.1  # Learning rate for engagement
        self.engagement_score = (1 - alpha) * self.engagement_score + alpha * (weight * performance_factor)
        self.engagement_score = max(0.0, min(1.0, self.engagement_score))
        self.save(update_fields=['engagement_score'])
        
        return self.engagement_score
