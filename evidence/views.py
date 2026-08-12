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
            queryset = queryset
