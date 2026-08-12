"""
Intelligence Views
API endpoints for the Intelligence Engine
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.core.cache import cache

from .models import StudentIntelligenceProfile
from .serializers import (
    StudentIntelligenceProfileSerializer,
    LearningEventSerializer,
    ClosedLoopResponseSerializer,
    MasteryStatusSerializer,
)
from .services import IntelligenceService, ClosedLoopService, RAGService


class IntelligenceViewSet(viewsets.GenericViewSet):
    """
    Main Intelligence API endpoints.
    """
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        return StudentIntelligenceProfileSerializer
    
    @action(detail=False, methods=['post'])
    def process_event(self, request):
        """
        Process a learning event through the closed-loop.
        
        This is the main endpoint for all learning interactions.
        """
        serializer = LearningEventSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Execute closed-loop
        loop_service = ClosedLoopService(request.user)
        result = loop_service.execute_loop(serializer.validated_data)
        
        response_serializer = ClosedLoopResponseSerializer(result)
        return Response(response_serializer.data)
    
    @action(detail=False, methods=['get'])
    def profile(self, request):
        """
        Get the user's intelligence profile.
        """
        profile = get_object_or_404(
            StudentIntelligenceProfile,
            user=request.user
        )
        serializer = StudentIntelligenceProfileSerializer(profile)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def mastery(self, request):
        """
        Get mastery status for all concepts.
        """
        profile = get_object_or_404(
            StudentIntelligenceProfile,
            user=request.user
        )
        
        # Get mastery data
        concept_ids = request.query_params.getlist('concept_ids')
        
        if concept_ids:
            mastery_data = {}
            for concept_id in concept_ids:
                mastery_data[concept_id] = profile.get_mastery_for_concept(concept_id)
        else:
            mastery_data = profile.concept_mastery
        
        return Response({
            'user_id': str(request.user.id),
            'concept_mastery': mastery_data,
            'topic_mastery': profile.topic_mastery,
            'subject_mastery': profile.subject_mastery,
            'weaknesses': profile.weaknesses,
        })
    
    @action(detail=False, methods=['get'])
    def next_action(self, request):
        """
        Get the next recommended action without processing an event.
        """
        profile = get_object_or_404(
            StudentIntelligenceProfile,
            user=request.user
        )
        
        from intelligence.engines import NextBestActionEngine
        engine = NextBestActionEngine(profile)
        action = engine.get_next_action({
            'current_concept_id': request.query_params.get('concept_id'),
            'context': request.query_params.get('context'),
        })
        
        return Response(action)
    
    @action(detail=False, methods=['get'])
    def learning_path(self, request):
        """
        Get personalized learning path.
        """
        service = IntelligenceService(request.user)
        subject_id = request.query_params.get('subject_id')
        
        path = service.get_learning_path(subject_id)
        return Response(path)
    
    @action(detail=False, methods=['post'])
    def rag_retrieve(self, request):
        """
        Retrieve personalized content using RAG.
        """
        query = request.data.get('query')
        if not query:
            return Response(
                {'error': 'query is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        rag_service = RAGService(request.user)
        results = rag_service.retrieve_content(
            query=query,
            context=request.data.get('context', {}),
            max_results=request.data.get('max_results', 5)
        )
        
        return Response({
            'query': query,
            'results': results,
            'count': len(results),
        })
    
    @action(detail=False, methods=['get'])
    def analytics(self, request):
        """
        Get learning analytics.
        """
        from intelligence.engines import MasteryEngine
        
        profile = get_object_or_404(
            StudentIntelligenceProfile,
            user=request.user
        )
        
        engine = MasteryEngine(profile)
        analytics = engine.get_mastery_analytics()
        
        # Add engagement analytics
        analytics['engagement'] = {
            'score': profile.engagement_score,
            'consistency': profile.consistency_score,
            'curiosity': profile.curiosity_score,
            'study_streak': profile.study_streak_days,
            'last_activity': profile.last_activity_date,
        }
        
        # Add progress analytics
        analytics['progress'] = {
            'total_attempts': profile.total_attempts,
            'total_correct': profile.total_correct,
            'average_score': profile.average_score,
            'growth_rate': profile.knowledge_growth_rate,
        }
        
        return Response(analytics)
    
    @action(detail=False, methods=['post'])
    def update_goals(self, request):
        """
        Update learning goals.
        """
        goals = request.data.get('goals', [])
        if not goals:
            return Response(
                {'error': 'goals list is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        profile = get_object_or_404(
            StudentIntelligenceProfile,
            user=request.user
        )
        
        profile.learning_goals = goals
        profile.save()
        
        return Response({
            'status': 'updated',
            'goals': goals,
        })
    
    @action(detail=False, methods=['post'])
    def update_preferences(self, request):
        """
        Update learning preferences.
        """
        preferences = request.data.get('preferences', [])
        
        profile = get_object_or_404(
            StudentIntelligenceProfile,
            user=request.user
        )
        
        profile.preferred_learning_styles = preferences
        profile.save()
        
        return Response({
            'status': 'updated',
            'preferences': preferences,
        })
