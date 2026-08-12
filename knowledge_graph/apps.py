from django.apps import AppConfig


class KnowledgeGraphConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'knowledge_graph'
    verbose_name = 'Knowledge Graph'
    
    def ready(self):
        """Initialize the knowledge graph service when Django starts."""
        import knowledge_graph.services
        # Optionally preload graph data
        # knowledge_graph.services.KnowledgeGraphService.preload_cache()
