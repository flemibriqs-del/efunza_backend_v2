from django.core.management.base import BaseCommand, CommandError
import json
from pathlib import Path

class Command(BaseCommand):
    help = 'Ingest simulator log JSON files and create SimulatorLog entries.'

    def add_arguments(self, parser):
        parser.add_argument('--path', required=True, help='Path to directory containing simulator JSON logs')

    def handle(self, *args, **options):
        path = Path(options['path'])
        if not path.exists():
            raise CommandError(f'Path not found: {path}')

        try:
            from maritime.models import SimulatorLog
            from django.contrib.auth import get_user_model
        except Exception as e:
            self.stdout.write(self.style.WARNING('SimulatorLog model not available or import failed.'))
            self.stdout.write(self.style.WARNING(str(e)))
            return

        files = [f for f in path.glob('**/*.json') if f.is_file()]
        count = 0
        for f in files:
            try:
                data = json.loads(f.read_text(encoding='utf-8'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'Failed to parse {f}: {e}'))
                continue

            run_id = data.get('run_id') or f.stem
            telemetry = data.get('telemetry', {})
            transcript = data.get('transcript', '')
            metadata = data.get('metadata', {})
            user_identifier = data.get('user')
            user = None
            if user_identifier:
                User = get_user_model()
                try:
                    # try by username or id
                    if isinstance(user_identifier, int):
                        user = User.objects.filter(id=user_identifier).first()
                    else:
                        user = User.objects.filter(username=user_identifier).first()
                except Exception:
                    user = None

            SimulatorLog.objects.create(
                user=user,
                run_id=run_id,
                telemetry=telemetry,
                transcript=transcript,
                metadata=metadata,
            )
            count += 1

        self.stdout.write(self.style.SUCCESS(f'Ingested {count} simulator logs from {len(files)} files'))
