from django.contrib import admin
from django.utils.html import format_html
from .models import CompetencyFramework, Competency, CompetencyEvidence, CompetencyAssessment


@admin.register(CompetencyFramework)
class CompetencyFrameworkAdmin(admin.ModelAdmin):
    list_display = ['name', 'domain', 'version', 'is_active']
    list_filter = ['domain', 'is_active']
    search_fields = ['name', 'description']


@admin.register(Competency)
class CompetencyAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'framework', 'level', 'is_active']
    list_filter = ['framework', 'level', 'is_active']
    search_fields = ['code', 'name', 'description']
    filter_horizontal = ['prerequisites']


@admin.register(CompetencyEvidence)
class CompetencyEvidenceAdmin(admin.ModelAdmin):
    list_display = ['user', 'activity_name', 'activity_type', 'performance_score', 'status', 'completed_at']
    list_filter = ['activity_type', 'status', 'domain']
    search_fields = ['user__email', 'activity_name', 'activity_id']
    readonly_fields = ['id', 'created_at', 'updated_at', 'quality_score']
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editing existing
            return self.readonly_fields + ['user', 'activity_id']
        return self.readonly_fields


@admin.register(CompetencyAssessment)
class CompetencyAssessmentAdmin(admin.ModelAdmin):
    list_display = ['user', 'competency', 'level_achieved', 'confidence_score', 'assessed_at']
    list_filter = ['level_achieved', 'assessment_method']
    search_fields = ['user__email', 'competency__name', 'competency__code']
    filter_horizontal = ['evidence_used']
