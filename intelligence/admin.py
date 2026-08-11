from django.contrib import admin
from .models import Competency, CompetencyMapping, ItemAttempt, EmbeddingRecord


@admin.register(Competency)
class CompetencyAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'taxonomy_level', 'created_at')
    search_fields = ('code', 'name')


@admin.register(CompetencyMapping)
class CompetencyMappingAdmin(admin.ModelAdmin):
    list_display = ('competency', 'source_type', 'source_id', 'weight')
    list_filter = ('source_type',)


@admin.register(ItemAttempt)
class ItemAttemptAdmin(admin.ModelAdmin):
    list_display = ('user', 'assessment', 'question_index', 'score', 'started_at', 'finished_at')
    search_fields = ('user__username',)
    list_filter = ('assessment',)


@admin.register(EmbeddingRecord)
class EmbeddingRecordAdmin(admin.ModelAdmin):
    list_display = ('source_type', 'source_id', 'chunk_index', 'created_at')
    search_fields = ('source_type',)
