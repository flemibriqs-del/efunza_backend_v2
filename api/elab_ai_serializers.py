from rest_framework import serializers
from .elab_ai_models import ELabProject, ELabMilestone, StudentAIInsight, AIChatLog

class ELabMilestoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = ELabMilestone
        fields = "__all__"

class ELabProjectSerializer(serializers.ModelSerializer):
    milestones = ELabMilestoneSerializer(many=True, read_only=True)
    student_name = serializers.CharField(source="student.username", read_only=True)

    class Meta:
        model = ELabProject
        fields = "__all__"
        read_only_fields = ["student", "innovation_score", "ai_summary"]

class StudentAIInsightSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentAIInsight
        fields = "__all__"

class AIChatLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIChatLog
        fields = "__all__"
