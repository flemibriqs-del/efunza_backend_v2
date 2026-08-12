from rest_framework import serializers
from .models import Subject, Topic, Concept


class SubjectSerializer(serializers.ModelSerializer):
    """Serializer for Subject model."""
    topic_count = serializers.IntegerField(read_only=True)
    total_concepts = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Subject
        fields = [
            'id', 'name', 'code', 'description', 'icon', 'domain',
            'order', 'is_active', 'image_url', 'meta_data',
            'topic_count', 'total_concepts', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class TopicSerializer(serializers.ModelSerializer):
    """Serializer for Topic model."""
    concept_count = serializers.IntegerField(read_only=True)
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    
    class Meta:
        model = Topic
        fields = [
            'id', 'name', 'description', 'difficulty_level',
            'estimated_study_time', 'order', 'is_active',
            'subject', 'subject_name', 'prerequisites',
            'concept_count', 'meta_data', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ConceptSerializer(serializers.ModelSerializer):
    """Serializer for Concept model."""
    topic_name = serializers.CharField(source='topic.name', read_only=True)
    difficulty_display = serializers.CharField(source='get_difficulty_display', read_only=True)
    prerequisite_count = serializers.SerializerMethodField()
    dependent_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Concept
        fields = [
            'id', 'name', 'description', 'difficulty', 'difficulty_display',
            'is_core', 'order', 'is_active',
            'topic', 'topic_name',
            'prerequisites', 'skills',
            'learning_objectives', 'key_terms', 'example_problems',
            'common_misconceptions', 'mastery_threshold',
            'recommended_assessment_count',
            'prerequisite_count', 'dependent_count',
            'meta_data', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_prerequisite_count(self, obj):
        return obj.prerequisites.count()
    
    def get_dependent_count(self, obj):
        return obj.dependents.count()


class ConceptDetailSerializer(ConceptSerializer):
    """Detailed concept serializer with nested relationships."""
    prerequisites_detail = ConceptSerializer(source='prerequisites', many=True, read_only=True)
    dependents_detail = ConceptSerializer(source='dependents', many=True, read_only=True)
    
    class Meta(ConceptSerializer.Meta):
        fields = ConceptSerializer.Meta.fields + [
            'prerequisites_detail',
            'dependents_detail',
        ]


class SubjectDetailSerializer(SubjectSerializer):
    """Detailed subject serializer with nested topics."""
    topics = TopicSerializer(many=True, read_only=True)
    
    class Meta(SubjectSerializer.Meta):
        fields = SubjectSerializer.Meta.fields + ['topics']


class TopicDetailSerializer(TopicSerializer):
    """Detailed topic serializer with nested concepts."""
    concepts = ConceptSerializer(many=True, read_only=True)
    prerequisites_detail = TopicSerializer(source='prerequisites', many=True, read_only=True)
    
    class Meta(TopicSerializer.Meta):
        fields = TopicSerializer.Meta.fields + [
            'concepts',
            'prerequisites_detail',
        ]
