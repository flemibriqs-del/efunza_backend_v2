from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SubjectViewSet, TopicViewSet, ConceptViewSet

router = DefaultRouter()
router.register(r'subjects', SubjectViewSet, basename='subject')
router.register(r'topics', TopicViewSet, basename='topic')
router.register(r'concepts', ConceptViewSet, basename='concept')

urlpatterns = [
    path('', include(router.urls)),
]
