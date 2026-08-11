from django.db import models
from django.contrib.auth.models import User

class ELabProject(models.Model):
    STAGE_CHOICES = [
        ("idea", "Idea"),
        ("research", "Research"),
        ("prototype", "Prototype"),
        ("testing", "Testing"),
        ("report", "Report"),
        ("pitch", "Pitch"),
        ("completed", "Completed"),
    ]

    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="ai_elab_projects")
    title = models.CharField(max_length=255)
    problem_statement = models.TextField(blank=True)
    category = models.CharField(max_length=120, blank=True, default="Science Fair")
    stage = models.CharField(max_length=30, choices=STAGE_CHOICES, default="idea")
    materials = models.TextField(blank=True)
    method = models.TextField(blank=True)
    expected_outcome = models.TextField(blank=True)
    innovation_score = models.PositiveIntegerField(default=0)
    ai_summary = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

class ELabMilestone(models.Model):
    project = models.ForeignKey(ELabProject, on_delete=models.CASCADE, related_name="milestones")
    title = models.CharField(max_length=255)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=40, default="open")
    due_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.title

class StudentAIInsight(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="ai_insights")
    weak_topics = models.JSONField(default=list, blank=True)
    strengths = models.JSONField(default=list, blank=True)
    career_matches = models.JSONField(default=list, blank=True)
    learning_style = models.CharField(max_length=120, blank=True)
    innovation_score = models.PositiveIntegerField(default=0)
    ai_recommendation = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

class AIChatLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    agent = models.CharField(max_length=80, default="tutor")
    module = models.CharField(max_length=80, default="general")
    prompt = models.TextField()
    response = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
