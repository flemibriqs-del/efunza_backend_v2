"""
Intelligence Serializers
"""

from rest_framework import serializers
from .models import StudentIntelligenceProfile


class StudentIntelligenceProfileSerializer(serializers.ModelSerializer):
    """Serializer for StudentIntelligenceProfile."""
    
    class Meta:
        model = StudentIntelligenceProfile
        fields = [
            'id', 'user', 'learning_goals', 'preferred_learning_styles',
            'career_interests', 'current_learning_path',
            'concept_mastery', 'topic_mastery', 'subject_mastery',
            'skills', 'competencies', 'weaknesses',
            'total_attempts', 'total_correct', 'average_score',
            'study_streak_days', 'last_activity_date',
            'engagement_score', 'consistency_score', 'curiosity_score',
            'knowledge_growth_rate', 'predicted_learning_speed',
            'career_readiness_level', 'recommended_career_paths',
            'created_at', 'updated_at', 'version',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'version']


class LearningEventSerializer(serializers.Serializer):
    """Serializer for learning events."""
    
    event_type = serializers.ChoiceField(
        choices=['quiz', 'simulation', 'practical', 'project', 
                 'discussion', 'peer_review', 'self_assessment', 
                 'exam', 'portfolio', 'internship']
    )
    event_id = serializers.CharField(max_length=100, required=False, allow_blank=True)
    event_name = serializers.CharField(max_length=200, required=False, allow_blank=True)
    concepts = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        default=list
    )
    performance_score = serializers.FloatField(
        min_value=0, max_value=100,
        required=False,
        default=0
    )
    difficulty_level = serializers.IntegerField(
        min_value=1, max_value=10,
        required=False,
        default=3
    )
    time_spent = serializers.IntegerField(
        required=False,
        default=0,
        help_text="Time spent in seconds"
    )
    domain = serializers.CharField(required=False, default='general', allow_blank=True)
    tags = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list
    )
    metadata = serializers.DictField(required=False, default=dict)
    skill_ids = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list
    )
    context = serializers.DictField(required=False, default=dict)


class ClosedLoopResponseSerializer(serializers.Serializer):
    """Serializer for closed-loop response."""
    
    user_id = serializers.CharField()
    start_time = serializers.CharField()
    end_time = serializers.CharField()
    duration = serializers.FloatField()
    status = serializers.CharField()
    steps = serializers.DictField()
    next_action = serializers.DictField()
    summary = serializers.DictField()


class MasteryStatusSerializer(serializers.Serializer):
    """Serializer for mastery status."""
    
    concept_id = serializers.CharField()
    mastery = serializers.FloatField()
    status = serializers.CharField()
    attempt_count = serializers.IntegerField()
    average_score = serializers.FloatField()
    consistency = serializers.FloatField()
    last_attempt = serializers.DateTimeField(required=False, allow_null=True)
    needs_remediation = serializers.BooleanField()
    threshold = serializers.FloatField()
