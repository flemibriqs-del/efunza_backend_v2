from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CompetencyFrameworkViewSet, CompetencyViewSet,
    CompetencyEvidenceViewSet, CompetencyAssessmentViewSet
)

router = DefaultRouter()
router.register(r'frameworks', CompetencyFrameworkViewSet, basename='framework')
router.register(r'competencies', CompetencyViewSet, basename='competency')
router.register(r'evidence', CompetencyEvidenceViewSet, basename='evidence')
router.register(r'assessments', CompetencyAssessmentViewSet, basename='assessment')

urlpatterns = [
    path('', include(router.urls)),
]
