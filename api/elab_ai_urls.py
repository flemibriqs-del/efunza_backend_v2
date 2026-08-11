from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .elab_ai_views import (
    ELabProjectViewSet, ELabMilestoneViewSet, StudentAIInsightViewSet,
    ai_chat, generate_student_insight, ai_elab_health
)

router = DefaultRouter()
router.register(r"elab-projects", ELabProjectViewSet, basename="elab-project")
router.register(r"elab-milestones", ELabMilestoneViewSet, basename="elab-milestone")
router.register(r"student-ai-insights", StudentAIInsightViewSet, basename="student-ai-insight")

urlpatterns = [
    path("ai-elab/health/", ai_elab_health),
    path("ai/chat/", ai_chat),
    path("ai/student-insight/", generate_student_insight),
    path("", include(router.urls)),
]
