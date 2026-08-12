"""
Intelligence URLs
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import IntelligenceViewSet

router = DefaultRouter()
router.register(r'intelligence', IntelligenceViewSet, basename='intelligence')

urlpatterns = [
    path('', include(router.urls)),
]
