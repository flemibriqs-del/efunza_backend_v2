from rest_framework import serializers
from .models import (
    CompetencyFramework, Competency, CompetencyEvidence, 
    CompetencyAssessment, EvidenceTransaction
)


class CompetencyFrameworkSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompetencyFramework
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class CompetencySerializer(serializers.ModelSerializer):
    class Meta:
        model = Competency
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class CompetencyEvidenceSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    verified_by_email = serializers.EmailField(source='verified_by.email', read_only=True)
    
    class Meta:
        model = CompetencyEvidence
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'quality_score', 'user']


class CompetencyEvidenceCreateSerializer(serializers.Serializer):
    activity_type = serializers.ChoiceField(choices=CompetencyEvidence._meta.get_field('activity_type').choices)
    activity_id = serializers.CharField(max_length=100)
    activity_name = serializers.CharField(max_length=200)
    performance_score = serializers.FloatField(min_value=0, max_value=100)
    difficulty_level = serializers.IntegerField(min_value=1, max_value=10)
    completed_at = serializers.DateTimeField(required=False)
    concepts = serializers.ListField(child=serializers.DictField(), required=False)
    domain = serializers.CharField(required=False)
    evidence_data = serializers.DictField(required=False)
    context = serializers.DictField(required=False)
    tags = serializers.ListField(child=serializers.CharField(), required=False)


class CompetencyAssessmentSerializer(serializers.ModelSerializer):
    competency_name = serializers.CharField(source='competency.name', read_only=True)
    competency_code = serializers.CharField(source='competency.code', read_only=True)
    
    class Meta:
        model = CompetencyAssessment
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class EvidenceTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = EvidenceTransaction
        fields = '__all__'
        read_only_fields = ['id', 'created_at']


class CompetencyProfileSerializer(serializers.Serializer):
    """Serializer for competency profile response."""
    user_id = serializers.CharField()
    assessments = CompetencyAssessmentSerializer(many=True)
    summary = serializers.DictField()
