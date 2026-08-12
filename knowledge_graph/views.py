from django.db.models import Prefetch, Count, Q
from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404

from .models import Subject, Topic, Concept
from .serializers import (
    SubjectSerializer, SubjectDetailSerializer,
    TopicSerializer, TopicDetailSerializer,
    ConceptSerializer, ConceptDetailSerializer
)
from .services import KnowledgeGraphService


class SubjectViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing subjects.
    """
    queryset = Subject.objects.prefetch_related('topics').filter(is_active=True)
    serializer_class = SubjectSerializer
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAuthenticated()]
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return SubjectDetailSerializer
        return SubjectSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        domain = self.request.query_params.get('domain')
        if domain:
            queryset = queryset.filter(domain=domain)
        return queryset
    
    @action(detail=True, methods=['get'])
    def learning_path(self, request, pk=None):
        """Get the learning path for a subject."""
        subject = self.get_object()
        path = KnowledgeGraphService.get_learning_path(subject_id=subject.id)
        return Response(path)
    
    @action(detail=True, methods=['get'])
    def topics_with_progress(self, request, pk=None):
        """Get topics with progress for a user."""
        subject = self.get_object()
        topics = subject.topics.filter(is_active=True)
        topics_data = KnowledgeGraphService.get_topics_with_progress(
            topics=topics,
            user=request.user if request.user.is_authenticated else None
        )
        return Response(topics_data)


class TopicViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing topics.
    """
    queryset = Topic.objects.select_related('subject').prefetch_related('concepts')
    serializer_class = TopicSerializer
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAuthenticated()]
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return TopicDetailSerializer
        return TopicSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        subject_id = self.request.query_params.get('subject_id')
        if subject_id:
            queryset = queryset.filter(subject_id=subject_id)
        
        difficulty = self.request.query_params.get('difficulty')
        if difficulty:
            queryset = queryset.filter(difficulty_level=difficulty)
        
        return queryset
    
    @action(detail=True, methods=['get'])
    def prerequisites(self, request, pk=None):
        """Get all prerequisites for a topic."""
        topic = self.get_object()
        prerequisites = topic.get_prerequisites_chain()
        serializer = TopicSerializer(prerequisites, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def concepts_with_mastery(self, request, pk=None):
        """Get concepts with mastery data for a user."""
        topic = self.get_object()
        concepts = topic.concepts.filter(is_active=True)
        concept_data = KnowledgeGraphService.get_concepts_with_mastery(
            concepts=concepts,
            user=request.user if request.user.is_authenticated else None
        )
        return Response(concept_data)


class ConceptViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing concepts.
    """
    queryset = Concept.objects.select_related('topic').prefetch_related(
        'prerequisites', 'dependents', 'skills'
    )
    serializer_class = ConceptSerializer
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAuthenticated()]
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ConceptDetailSerializer
        return ConceptSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        topic_id = self.request.query_params.get('topic_id')
        if topic_id:
            queryset = queryset.filter(topic_id=topic_id)
        
        difficulty = self.request.query_params.get('difficulty')
        if difficulty:
            queryset = queryset.filter(difficulty=difficulty)
        
        is_core = self.request.query_params.get('is_core')
        if is_core is not None:
            queryset = queryset.filter(is_core=is_core.lower() == 'true')
        
        return queryset
    
    @action(detail=True, methods=['get'])
    def prerequisites_chain(self, request, pk=None):
        """Get all prerequisites recursively."""
        concept = self.get_object()
        prerequisites = concept.get_prerequisites_chain()
        serializer = ConceptSerializer(prerequisites, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def dependents(self, request, pk=None):
        """Get all concepts that depend on this concept."""
        concept = self.get_object()
        dependents = concept.get_dependent_concepts()
        serializer = ConceptSerializer(dependents, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def next_concepts(self, request, pk=None):
        """Get recommended next concepts."""
        concept = self.get_object()
        next_concepts = concept.get_recommended_next_concepts()
        serializer = ConceptSerializer(next_concepts, many=True)
        return Response(serializer.data)
