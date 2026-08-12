from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from .models import CompetencyFramework, Competency, CompetencyEvidence, CompetencyAssessment
from .serializers import (
    CompetencyFrameworkSerializer, CompetencySerializer,
    CompetencyEvidenceSerializer, CompetencyEvidenceCreateSerializer,
    CompetencyAssessmentSerializer, CompetencyProfileSerializer
)
from .engines.competency_engine import CompetencyEngine
from .services import EvidenceService


class CompetencyFrameworkViewSet(viewsets.ModelViewSet):
    """
    ViewSet for competency frameworks.
    """
    queryset = CompetencyFramework.objects.filter(is_active=True)
    serializer_class = CompetencyFrameworkSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        domain = self.request.query_params.get('domain')
        if domain:
            queryset = queryset.filter(domain=domain)
        return queryset


class CompetencyViewSet(viewsets.ModelViewSet):
    """
    ViewSet for competencies.
    """
    queryset = Competency.objects.filter(is_active=True)
    serializer_class = CompetencySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        framework_id = self.request.query_params.get('framework_id')
        if framework_id:
            queryset = queryset.filter(framework_id=framework_id)
        
        level = self.request.query_params.get('level')
        if level:
            queryset = queryset.filter(level=level)
        
        return queryset


class CompetencyEvidenceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for competency evidence.
    """
    serializer_class = CompetencyEvidenceSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return CompetencyEvidence.objects.filter(user=self.request.user)
    
    def create(self, request, *args, **kwargs):
        """Create evidence from learning activity."""
        serializer = CompetencyEvidenceCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Process evidence
        engine = CompetencyEngine(request.user)
        evidence = engine.process_evidence(serializer.validated_data)
        
        response_serializer = CompetencyEvidenceSerializer(evidence)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def verify(self, request, pk=None):
        """Verify evidence."""
        evidence = self.get_object()
        engine = CompetencyEngine(request.user)
        
        notes = request.data.get('notes', '')
        verified_evidence = engine.verify_evidence(
            evidence_id=evidence.id,
            verifier=request.user,
            notes=notes
        )
        
        serializer = CompetencyEvidenceSerializer(verified_evidence)
        return Response(serializer.data)


class CompetencyAssessmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for competency assessments.
    """
    queryset = CompetencyAssessment.objects.all()
    serializer_class = CompetencyAssessmentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return CompetencyAssessment.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def profile(self, request):
        """Get user's competency profile."""
        engine = CompetencyEngine(request.user)
        profile = engine.get_competency_profile()
        
        serializer = CompetencyProfileSerializer(profile)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def recommendations(self, request):
        """Get evidence recommendations."""
        engine = CompetencyEngine(request.user)
        recommendations = engine.get_evidence_recommendations()
        return Response(recommendations)
