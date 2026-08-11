from django.db import models
from django.conf import settings
from django.utils import timezone


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Competency(TimeStampedModel):
    code = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    taxonomy_level = models.CharField(max_length=50, blank=True)
    prerequisites = models.ManyToManyField('self', blank=True, symmetrical=False, related_name='dependents')

    class Meta:
        ordering = ['code']

    def __str__(self):
        return f"{self.code} - {self.name}"


class CompetencyMapping(TimeStampedModel):
    SOURCE_TYPES = (
        ('assessment', 'Assessment'),
        ('lesson', 'Lesson'),
        ('book', 'Book'),
        ('content', 'ContentItem'),
    )

    competency = models.ForeignKey(Competency, on_delete=models.CASCADE, related_name='mappings')
    source_type = models.CharField(max_length=50, choices=SOURCE_TYPES)
    source_id = models.IntegerField()
    weight = models.FloatField(default=1.0)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        indexes = [models.Index(fields=['source_type', 'source_id'])]

    def __str__(self):
        return f"{self.source_type}:{self.source_id} -> {self.competency.code}"


class ItemAttempt(TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='item_attempts')
    assessment = models.ForeignKey('api.Assessment', on_delete=models.CASCADE, null=True, blank=True)
    question_index = models.IntegerField()
    submitted_answer = models.JSONField(default=dict, blank=True)
    score = models.FloatField(null=True, blank=True)
    started_at = models.DateTimeField(default=timezone.now)
    finished_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        indexes = [models.Index(fields=['user', 'assessment', 'question_index'])]

    def __str__(self):
        return f"Attempt: user={self.user_id} assessment={self.assessment_id} q={self.question_index}"


class EmbeddingRecord(TimeStampedModel):
    SOURCE_TYPES = (
        ('book', 'Book'),
        ('lesson', 'Lesson'),
        ('content', 'ContentItem'),
    )

    source_type = models.CharField(max_length=50, choices=SOURCE_TYPES)
    source_id = models.IntegerField(null=True, blank=True)
    chunk_index = models.IntegerField(default=0)
    text = models.TextField(blank=True)
    vector = models.JSONField(default=list, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        indexes = [models.Index(fields=['source_type', 'source_id', 'chunk_index'])]

    def __str__(self):
        return f"Embedding {self.source_type}:{self.source_id}#{self.chunk_index}"
