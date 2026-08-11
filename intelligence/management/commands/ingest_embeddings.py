from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import transaction
import math, logging

logger = logging.getLogger(__name__)

CHUNK_SIZE = 1000

class Command(BaseCommand):
    help = 'Ingest text content (Books, Lessons, ContentItem) and create embedding records using OpenAI embeddings. Stores vectors as JSON in EmbeddingRecord (for prototyping).'

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=0, help='Limit number of records per source (0 = no limit)')

    def handle(self, *args, **options):
        limit = options.get('limit', 0) or 0

        try:
            from openai import OpenAI
        except Exception:
            OpenAI = None

        client = None
        if getattr(settings, 'OPENAI_API_KEY', '') and OpenAI is not None:
            client = OpenAI(api_key=settings.OPENAI_API_KEY)
            embedding_model = getattr(settings, 'OPENAI_EMBEDDING_MODEL', 'text-embedding-3-small')
        else:
            client = None
            embedding_model = None

        # Lazy import to avoid startup dependency
        from api.models import Book, Lesson, ContentItem
        from intelligence.models import EmbeddingRecord

        sources = [
            ('book', Book, 'text_content'),
            ('lesson', Lesson, 'content'),
            ('content', ContentItem, 'body'),
        ]

        total = 0
        for source_type, Model, text_field in sources:
            qs = Model.objects.all()
            if limit > 0:
                qs = qs[:limit]

            for obj in qs:
                text = getattr(obj, text_field, '') or ''
                if not text:
                    continue

                # Simple chunking by characters
                chunks = [text[i:i+CHUNK_SIZE] for i in range(0, len(text), CHUNK_SIZE)]

                for idx, chunk in enumerate(chunks):
                    vec = []
                    if client and embedding_model:
                        try:
                            resp = client.embeddings.create(
                                model=embedding_model,
                                input=chunk
                            )
                            vec = resp.data[0].embedding
                        except Exception as e:
                            logger.error(f"Embedding generation failed for {source_type} {obj.id} chunk {idx}: {e}")
                            vec = []

                    # Save or update embedding
                    with transaction.atomic():
                        EmbeddingRecord.objects.update_or_create(
                            source_type=source_type,
                            source_id=obj.id,
                            chunk_index=idx,
                            defaults={
                                'text': chunk[:10000],
                                'vector': vec or [],
                                'metadata': {'source_model': Model.__name__}
                            }
                        )
                    total += 1

        self.stdout.write(self.style.SUCCESS(f'Ingest complete. {total} chunks processed.'))
