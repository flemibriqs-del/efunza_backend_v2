# api/management/commands/backfill_access_codes.py
import hashlib
from django.core.management.base import BaseCommand
from api.maritime_models import MaritimeEnrollment
from django.utils import timezone

class Command(BaseCommand):
    help = "Backfill access_code_hash from legacy plaintext access_code, then optionally clear plaintext."

    def add_arguments(self, parser):
        parser.add_argument('--clear-plaintext', action='store_true', help='Clear legacy plaintext access_code after backfill.')

    def handle(self, *args, **options):
        clear = options['clear_plaintext']
        qs = MaritimeEnrollment.objects.filter(access_code__isnull=False).exclude(access_code='')
        total = qs.count()
        self.stdout.write(f"Found {total} enrollments with plaintext access_code.")
        updated = 0
        for e in qs:
            try:
                code_plain = e.access_code.strip()
                if not code_plain:
                    continue
                code_hash = hashlib.sha256(code_plain.encode('utf-8')).hexdigest()
                if not MaritimeEnrollment.objects.filter(access_code_hash=code_hash).exists():
                    e.access_code_hash = code_hash
                    # set expiry default to 7 days from now if none
                    if not e.access_code_expires_at:
                        e.access_code_expires_at = timezone.now() + timezone.timedelta(days=7)
                    e.access_code_sent = True
                    e.save(update_fields=['access_code_hash', 'access_code_expires_at', 'access_code_sent'])
                    updated += 1
                if clear:
                    e.access_code = ''
                    e.save(update_fields=['access_code'])
            except Exception as exc:
                self.stderr.write(f"Failed for enrollment {e.id}: {exc}")
        self.stdout.write(f"Backfilled {updated} enrollments.")