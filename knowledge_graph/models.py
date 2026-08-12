"""
Knowledge Graph Models
Defines the hierarchical structure of learning content:
Subjects → Topics → Concepts → Prerequisites → Skills → Careers
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import uuid
import json


class Subject(models.Model):
    """
    Top-level learning domain (e.g., Maritime, Energy, Health)
    """
    DOMAIN_CHOICES = [
        ('maritime', 'Maritime'),
        ('energy', 'Energy'),
        ('health', 'Health'),
        ('robotics', 'Robotics'),
        ('tvet', 'TVET'),
        ('science', 'Science Fair'),
        ('elab', 'E-Lab'),
        ('elite', 'Elite Campus'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, unique=True)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField()
    icon = models.CharField(max_length=50, blank=True)
    domain = models.CharField(max_length=50, choices=DOMAIN_CHOICES)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    image_url = models.URLField(max_length=500, blank=True)
    meta_data = models.JSONField(default=dict, help_text="Additional metadata")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['domain', 'order']
        indexes = [
            models.Index(fields=['domain', 'is_active']),
            models.Index(fields=['code']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_domain_display()})"
    
    def get_topic_count(self):
        return self.topics.filter(is_active=True).count()
    
    def get_total_concepts(self):
        return Concept.objects.filter(topic__subject=self, is_active=True).count()
    
    def get_learning_path(self):
        """Get the recommended learning path for this subject."""
        from .services import KnowledgeGraphService
        return KnowledgeGraphService.get_learning_path(subject_id=self.id)


class Topic(models.Model):
    """
    Major topic within a subject (e.g., Navigation, Engine Systems)
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='topics')
    name = models.CharField(max_length=200)
    description = models.TextField()
    difficulty_level = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        default=1
    )
    estimated_study_time = models.DurationField(null=True, blank=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    prerequisites = models.ManyToManyField(
        'self', 
        symmetrical=False, 
        blank=True, 
        related_name='dependent_topics'
    )
    meta_data = models.JSONField(default=dict, help_text="Additional metadata")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['subject', 'name']
        ordering = ['subject', 'order']
        indexes = [
            models.Index(fields=['subject', 'is_active']),
            models.Index(fields=['difficulty_level']),
        ]
    
    def __str__(self):
        return f"{self.subject.name} - {self.name}"
    
    def get_concept_count(self):
        return self.concepts.filter(is_active=True).count()
    
    def get_mastery_required(self):
        """Calculate minimum mastery score needed for this topic."""
        return 0.6 + (self.difficulty_level - 1) * 0.04  # 60% for level 1, up to 96% for level 10
    
    def get_prerequisites_chain(self):
        """Get all prerequisites recursively."""
        prerequisites = []
        for prereq in self.prerequisites.all():
            prerequisites.append(prereq)
            prerequisites.extend(prereq.get_prerequisites_chain())
        return list(set(prerequisites))
    
    def get_skills_required(self):
        """Get all skills required for this topic."""
        from .services import KnowledgeGraphService
        return KnowledgeGraphService.get_skills_for_topic(topic_id=self.id)


class Concept(models.Model):
    """
    Specific concept within a topic (e.g., Celestial Navigation, Diesel Engine)
    """
    DIFFICULTY_CHOICES = [
        (1, 'Beginner'),
        (2, 'Elementary'),
        (3, 'Intermediate'),
        (4, 'Upper Intermediate'),
        (5, 'Advanced'),
        (6, 'Expert'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='concepts')
    name = models.CharField(max_length=200)
    description = models.TextField()
    difficulty = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        default=1,
        choices=DIFFICULTY_CHOICES
    )
    is_core = models.BooleanField(default=False, help_text="Core concept required for advancement")
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    # Relationships
    prerequisites = models.ManyToManyField(
        'self', 
        symmetrical=False, 
        blank=True, 
        related_name='dependents'
    )
    skills = models.ManyToManyField(
        'skills.Skill', 
        blank=True, 
        related_name='concepts'
    )  # Note: You'll need to create skills app or use this later
    
    # Learning resources
    learning_objectives = models.JSONField(default=list, help_text="List of learning objectives")
    key_terms = models.JSONField(default=list, help_text="Key terms and definitions")
    example_problems = models.JSONField(default=list, help_text="Example problems")
    common_misconceptions = models.JSONField(default=list, help_text="Common misconceptions to address")
    
    # Assessment metadata
    recommended_assessment_count = models.PositiveIntegerField(default=3)
    mastery_threshold = models.FloatField(
        default=0.7,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        help_text="Score needed to demonstrate mastery"
    )
    
    meta_data = models.JSONField(default=dict, help_text="Additional metadata")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['topic', 'name']
        ordering = ['topic', 'order']
        indexes = [
            models.Index(fields=['topic', 'is_active']),
            models.Index(fields=['difficulty', 'is_core']),
        ]
    
    def __str__(self):
        return f"{self.topic.name} - {self.name}"
    
    def get_prerequisites_chain(self):
        """Get all prerequisites recursively."""
        prerequisites = []
        for prereq in self.prerequisites.all():
            prerequisites.append(prereq)
            prerequisites.extend(prereq.get_prerequisites_chain())
        return list(set(prerequisites))
    
    def get_dependent_concepts(self):
        """Get all concepts that depend on this concept."""
        return self.dependents.all()
    
    def get_skill_requirements(self):
        """Get all skills required for this concept."""
        return self.skills.all()
    
    def is_prerequisite_for(self, concept_id):
        """Check if this concept is a prerequisite for another concept."""
        other_concept = Concept.objects.get(id=concept_id)
        return self in other_concept.get_prerequisites_chain()
    
    def get_recommended_next_concepts(self):
        """
        Get concepts recommended to study after this one.
        """
        # Get concepts that have this as a prerequisite
        return Concept.objects.filter(prerequisites=self, is_active=True)
    
    def get_mastery_required(self):
        """Get the mastery threshold for this concept."""
        return self.mastery_threshold
