from django.contrib import admin
from django.utils.html import format_html
from .models import Subject, Topic, Concept


class BaseKnowledgeAdmin(admin.ModelAdmin):
    """Base admin class with common configurations."""
    readonly_fields = ['id', 'created_at', 'updated_at']
    list_per_page = 25


@admin.register(Subject)
class SubjectAdmin(BaseKnowledgeAdmin):
    list_display = ['name', 'code', 'domain', 'topic_count', 'is_active', 'created_at']
    list_filter = ['domain', 'is_active']
    search_fields = ['name', 'code', 'description']
    prepopulated_fields = {'code': ['name']}
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'code', 'domain', 'description', 'icon', 'image_url')
        }),
        ('Status & Organization', {
            'fields': ('order', 'is_active', 'meta_data')
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def topic_count(self, obj):
        """Display number of topics in the subject."""
        count = obj.topics.filter(is_active=True).count()
        return format_html('<span style="color: #2b8cbe;">{}</span>', count)
    topic_count.short_description = 'Active Topics'


@admin.register(Topic)
class TopicAdmin(BaseKnowledgeAdmin):
    list_display = ['name', 'subject', 'difficulty_level', 'concept_count', 'is_active']
    list_filter = ['subject', 'difficulty_level', 'is_active']
    search_fields = ['name', 'description']
    filter_horizontal = ['prerequisites']
    fieldsets = (
        ('Basic Information', {
            'fields': ('subject', 'name', 'description', 'difficulty_level')
        }),
        ('Learning Path', {
            'fields': ('prerequisites', 'estimated_study_time', 'order')
        }),
        ('Status', {
            'fields': ('is_active', 'meta_data')
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def concept_count(self, obj):
        count = obj.concepts.filter(is_active=True).count()
        return format_html('<span style="color: #2b8cbe;">{}</span>', count)
    concept_count.short_description = 'Active Concepts'


@admin.register(Concept)
class ConceptAdmin(BaseKnowledgeAdmin):
    list_display = ['name', 'topic', 'difficulty', 'is_core', 'mastery_threshold', 'is_active']
    list_filter = ['topic__subject', 'topic', 'difficulty', 'is_core', 'is_active']
    search_fields = ['name', 'description', 'learning_objectives']
    filter_horizontal = ['prerequisites', 'skills']
    fieldsets = (
        ('Basic Information', {
            'fields': ('topic', 'name', 'description', 'difficulty', 'is_core', 'order')
        }),
        ('Prerequisites & Skills', {
            'fields': ('prerequisites', 'skills')
        }),
        ('Learning Content', {
            'fields': ('learning_objectives', 'key_terms', 'example_problems', 'common_misconceptions')
        }),
        ('Assessment', {
            'fields': ('mastery_threshold', 'recommended_assessment_count')
        }),
        ('Status', {
            'fields': ('is_active', 'meta_data')
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        """Make certain fields read-only when editing existing objects."""
        if obj:  # Editing existing object
            return self.readonly_fields + ['id']
        return self.readonly_fields
