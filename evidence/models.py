"""
Evidence Models
Structured competency evidence from learning activities
Maps activities → evidence → competencies → proficiency levels
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import uuid

User = get_user_model()


class CompetencyFramework(models.Model):
    """
    Defines the competency framework structure
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField()
    version = models.CharField(max_length=20)
    domain = models.CharField(max_length=50, choices=[
        ('maritime', 'Maritime'),
        ('energy', 'Energy'),
        ('health', 'Health'),
        ('robotics', 'Robotics'),
        ('tvet', 'TVET'),
        ('science', 'Science Fair'),
        ('elab', 'E-Lab'),
        ('elite', 'Elite Campus'),
        ('general', 'General'),
    ])
    is_active = models.BooleanField(default=True)
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['domain', 'name']
        indexes = [
            models.Index(fields=['domain', 'is_active']),
            models.Index(fields=['name']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_domain_display()})"


class Competency(models.Model):
    """
    Individual competency within a framework
    """
    LEVEL_CHOICES = [
        ('beginner', 'Beginner'),
        ('developing', 'Developing'),
        ('proficient', 'Proficient'),
        ('advanced', 'Advanced'),
        ('expert', 'Expert'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    framework = models.ForeignKey(CompetencyFramework, on_delete=models.CASCADE, related_name='competencies')
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField()
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='beginner')
    prerequisites = models.ManyToManyField('self', symmetrical=False, blank=True, related_name='dependents')
    required_skills = models.JSONField(default=list, help_text="Skills required for this competency")
    assessment_criteria = models.JSONField(default=list, help_text="Criteria for assessment")
    evidence_types = models.JSONField(default=list, help_text="Types of evidence accepted")
    mastery_threshold = models.FloatField(
        default=0.7,
        validators=[MinValueValidator(0), MaxValueValidator(1)]
    )
    is_active = models.BooleanField(default=True)
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['framework', 'level', 'name']
        indexes = [
            models.Index(fields=['framework', 'is_active']),
            models.Index(fields=['code']),
            models.Index(fields=['level']),
        ]
    
    def __str__(self):
        return f"{self.code}: {self.name} ({self.get_level_display()})"


class CompetencyEvidence(models.Model):
    """
    Structured competency evidence from learning activities
    """
    EVIDENCE_STATUS = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
        ('expired', 'Expired'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='competency_evidence')
    
    # Activity source
    activity_type = models.CharField(max_length=50, choices=[
        ('quiz', 'Quiz'),
        ('simulation', 'Simulation'),
        ('practical', 'Practical Activity'),
        ('project', 'Project'),
        ('discussion', 'Discussion'),
        ('peer_review', 'Peer Review'),
        ('self_assessment', 'Self Assessment'),
        ('exam', 'Examination'),
        ('portfolio', 'Portfolio'),
        ('internship', 'Internship'),
    ])
    activity_id = models.CharField(max_length=100, help_text="ID of the source activity")
    activity_name = models.CharField(max_length=200)
    activity_url = models.URLField(max_length=500, blank=True)
    
    # Evidence content
    evidence_data = models.JSONField(default=dict, help_text="Structured evidence data")
    evidence_summary = models.TextField(blank=True, help_text="Human-readable summary")
    
    # Competency mapping
    competencies_demonstrated = models.JSONField(default=list, help_text="[{competency_id, level, confidence}]")
    skills_demonstrated = models.JSONField(default=list, help_text="[{skill_id, proficiency, confidence}]")
    
    # Performance metrics
    performance_score = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        default=0.0
    )
    time_spent = models.DurationField(null=True, blank=True)
    difficulty_level = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        default=3
    )
    quality_score = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        null=True, blank=True,
        help_text="Quality of evidence as assessed by AI or reviewer"
    )
    
    # Evidence context
    context_data = models.JSONField(default=dict, help_text="Learning context, domain, etc.")
    domain = models.CharField(max_length=50, blank=True, help_text="Subject domain")
    tags = models.JSONField(default=list, help_text="Searchable tags")
    
    # Verification
    status = models.CharField(max_length=20, choices=EVIDENCE_STATUS, default='draft')
    verified_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(
        User, 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL, 
        related_name='verified_evidence'
    )
    verification_notes = models.TextField(blank=True)
    verification_metadata = models.JSONField(default=dict)
    
    # Timestamps
    completed_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(null=True, blank=True, help_text="Evidence validity period")
    
    class Meta:
        indexes = [
            models.Index(fields=['user', 'activity_type', 'completed_at']),
            models.Index(fields=['user', 'status']),
            models.Index(fields=['user', 'verified_at']),
            models.Index(fields=['domain', 'status']),
            models.Index(fields=['activity_id']),
        ]
        ordering = ['-completed_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.activity_name} ({self.get_activity_type_display()})"
    
    def get_competency_level(self, competency_id):
        """Get the proficiency level for a specific competency."""
        for comp in self.competencies_demonstrated:
            if comp.get('competency_id') == str(competency_id):
                return comp.get('level', 'unknown')
        return None
    
    def get_skill_proficiency(self, skill_id):
        """Get the proficiency level for a specific skill."""
        for skill in self.skills_demonstrated:
            if skill.get('skill_id') == str(skill_id):
                return skill.get('proficiency', 0.0)
        return 0.0
    
    def is_verified(self):
        return self.status == 'verified'
    
    def is_valid(self):
        if self.expires_at:
            return timezone.now() <= self.expires_at
        return True
    
    def calculate_evidence_strength(self):
        """Calculate the strength/weight of this evidence."""
        base_weight = 1.0
        
        # Boost based on activity type
        activity_weights = {
            'exam': 1.5,
            'project': 1.4,
            'simulation': 1.3,
            'practical': 1.3,
            'portfolio': 1.4,
            'internship': 1.5,
            'quiz': 0.8,
            'discussion': 0.6,
            'peer_review': 0.7,
            'self_assessment': 0.5,
        }
        base_weight *= activity_weights.get(self.activity_type, 1.0)
        
        # Boost based on performance
        if self.performance_score >= 80:
            base_weight *= 1.3
        elif self.performance_score >= 60:
            base_weight *= 1.1
        
        # Boost if verified
        if self.status == 'verified':
            base_weight *= 1.5
        
        # Adjust for recency (newer evidence is more relevant)
        days_old = (timezone.now() - self.completed_at).days
        if days_old > 180:  # Older than 6 months
            base_weight *= 0.8
        elif days_old > 365:  # Older than 1 year
            base_weight *= 0.6
        
        return min(base_weight, 5.0)  # Cap at 5.0


class CompetencyAssessment(models.Model):
    """
    Assessment of competencies achieved by a user
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='competency_assessments')
    competency = models.ForeignKey(Competency, on_delete=models.CASCADE, related_name='assessments')
    
    # Assessment details
    level_achieved = models.CharField(max_length=20, choices=Competency.LEVEL_CHOICES)
    confidence_score = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        default=0.8
    )
    
    # Evidence used
    evidence_used = models.ManyToManyField(CompetencyEvidence, related_name='assessments')
    evidence_count = models.PositiveIntegerField(default=0)
    
    # Assessment metadata
    assessed_at = models.DateTimeField(default=timezone.now)
    assessed_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='made_assessments'
    )
    assessment_notes = models.TextField(blank=True)
    assessment_method = models.CharField(max_length=50, default='ai_engine')
    
    # Additional data
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user', 'competency']
        indexes = [
            models.Index(fields=['user', 'level_achieved']),
            models.Index(fields=['competency', 'level_achieved']),
            models.Index(fields=['assessed_at']),
        ]
        ordering = ['-assessed_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.competency.name} ({self.level_achieved})"


class EvidenceTransaction(models.Model):
    """
    Audit trail for evidence creation and updates
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    evidence = models.ForeignKey(CompetencyEvidence, on_delete=models.CASCADE, related_name='transactions')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='evidence_transactions')
    
    action = models.CharField(max_length=50, choices=[
        ('created', 'Created'),
        ('updated', 'Updated'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
        ('archived', 'Archived'),
        ('restored', 'Restored'),
    ])
    changes = models.JSONField(default=dict, help_text="Changes made")
    previous_state = models.JSONField(default=dict)
    new_state = models.JSONField(default=dict)
    
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['evidence', 'action']),
            models.Index(fields=['user', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.action} - {self.evidence.activity_name}"
