from django.core.management.base import BaseCommand, CommandError
import os
from pathlib import Path

class Command(BaseCommand):
    help = 'Ingest maritime materials (plain text or markdown) into EmbeddingRecord entries for RAG retrieval.'

    def add_arguments(self, parser):
        parser.add_argument('--path', required=True, help='Path to directory containing materials (txt/md/pdf)')

    def handle(self, *args, **options):
        path = options['path']
        p = Path(path)
        if not p.exists():
            raise CommandError(f'Path not found: {path}')

        try:
            from intelligence.models import EmbeddingRecord
            from api.ai_utils import chunk_text
        except Exception as e:
            self.stdout.write(self.style.WARNING('EmbeddingRecord or chunking utilities not available in this environment.'))
            self.stdout.write(self.style.WARNING(str(e)))
            return

        files = [f for f in p.glob('**/*') if f.is_file()]
        count = 0
        for f in files:
            # Only ingest text-like files for now
            if f.suffix.lower() not in ('.txt', '.md'):
                continue
            text = f.read_text(encoding='utf-8')
            chunks = chunk_text(text)
            for idx, chunk in enumerate(chunks):
                EmbeddingRecord.objects.create(
                    text=chunk,
                    source_type='maritime_manual',
                    source_id=str(f.name),
                    chunk_index=idx,
                )
                count += 1

        self.stdout.write(self.style.SUCCESS(f'Ingested {count} chunks from {len(files)} files'))
