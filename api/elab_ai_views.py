from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .elab_ai_models import ELabProject, ELabMilestone, StudentAIInsight, AIChatLog
from .elab_ai_serializers import ELabProjectSerializer, ELabMilestoneSerializer, StudentAIInsightSerializer, AIChatLogSerializer
from .ai_engine import run_ai

class ELabProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ELabProjectSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return ELabProject.objects.all().order_by("-updated_at")
        return ELabProject.objects.filter(student=user).order_by("-updated_at")

    def perform_create(self, serializer):
        serializer.save(student=self.request.user)

    @action(detail=True, methods=["post"])
    def ai_coach(self, request, pk=None):
        project = self.get_object()
        prompt = request.data.get(
            "prompt",
            "Act as my AI science fair mentor. Improve this idea, suggest materials, method, risks, budget, report structure and next steps."
        )
        context = {
            "title": project.title,
            "problem_statement": project.problem_statement,
            "category": project.category,
            "stage": project.stage,
            "materials": project.materials,
            "method": project.method,
            "expected_outcome": project.expected_outcome,
            "innovation_score": project.innovation_score,
        }
        response = run_ai("elab", prompt, context, module="elab_project")
        project.ai_summary = response
        project.save(update_fields=["ai_summary"])
        AIChatLog.objects.create(user=request.user, agent="elab", module="elab_project", prompt=prompt, response=response)
        return Response({"response": response, "project": ELabProjectSerializer(project).data})

    @action(detail=True, methods=["post"])
    def score_innovation(self, request, pk=None):
        project = self.get_object()
        prompt = "Score this student innovation out of 100. Consider originality, practicality, impact, engineering depth, research quality and presentation readiness."
        context = {
            "title": project.title,
            "problem_statement": project.problem_statement,
            "category": project.category,
            "stage": project.stage,
            "materials": project.materials,
            "method": project.method,
        }
        response = run_ai("elab", prompt, context, module="elab_project")
        heuristic = min(100, max(40, 55 + len(project.problem_statement or "") // 30 + len(project.title or "") // 10))
        project.innovation_score = heuristic
        project.ai_summary = response
        project.save(update_fields=["innovation_score", "ai_summary"])
        return Response({"innovation_score": heuristic, "ai_feedback": response})

class ELabMilestoneViewSet(viewsets.ModelViewSet):
    queryset = ELabMilestone.objects.all()
    serializer_class = ELabMilestoneSerializer
    permission_classes = [IsAuthenticated]

class StudentAIInsightViewSet(viewsets.ModelViewSet):
    serializer_class = StudentAIInsightSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return StudentAIInsight.objects.all()
        return StudentAIInsight.objects.filter(student=self.request.user)

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def ai_chat(request):
    agent = request.data.get("agent", "tutor")
    module = request.data.get("module", "general")
    prompt = (
        request.data.get("prompt")
        or request.data.get("message")
        or request.data.get("question")
        or ""
    )
    context = request.data.get("context", {}) or {}

    if not isinstance(context, dict):
        context = {"raw_context": context}

    if not prompt:
        return Response({"error": "Prompt is required"}, status=status.HTTP_400_BAD_REQUEST)

    response = run_ai(
        agent=agent,
        prompt=prompt,
        context=context,
        module=module
    )

    AIChatLog.objects.create(
        user=request.user,
        agent=agent,
        module=module,
        prompt=prompt,
        response=response
    )

    return Response({
        "answer": response,
        "reply": response,
        "message": response,
        "response": response,
        "source": "elab_ai_engine",
        "agent": agent,
        "module": module
    })

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def generate_student_insight(request):
    user = request.user
    projects = list(ELabProject.objects.filter(student=user).values("title", "category", "stage", "innovation_score")[:20])
    prompt = "Analyze this learner and generate weak topics, strengths, career matches, learning style and next actions."
    response = run_ai("career", prompt, {"elab_projects": projects}, module="student_intelligence")

    insight, _ = StudentAIInsight.objects.get_or_create(student=user)
    insight.career_matches = ["Engineering", "Technology", "Innovation", "Entrepreneurship"] if projects else ["Education", "Business", "Technology"]
    insight.learning_style = "project-based and visual"
    insight.ai_recommendation = response
    insight.innovation_score = max([p["innovation_score"] for p in projects], default=0)
    insight.save()

    return Response(StudentAIInsightSerializer(insight).data)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def ai_elab_health(request):
    return Response({
        "ok": True,
        "module": "AI E-Lab",
        "features": [
            "AI Project Mentor",
            "AI Experiment Designer",
            "AI Report Writer",
            "Innovation Scorer",
            "Career Intelligence"
        ]
    })

