from django.core.management.base import BaseCommand
from django.db import transaction
from intelligence.models import Competency, CompetencyMapping
from api.models import Lesson, Assessment

class Command(BaseCommand):
    help = 'Seed competencies based on Lesson.topic and Assessment.topic and create mappings.'

    def handle(self, *args, **options):
        created = 0
        topics = set()

        for lesson in Lesson.objects.exclude(topic__exact='').values_list('topic', flat=True):
            if lesson:
                topics.add(lesson.strip())

        for assessment in Assessment.objects.exclude(topic__exact='').values_list('topic', flat=True):
            if assessment:
                topics.add(assessment.strip())

        for t in sorted(topics):
            code = t.lower().replace(' ', '_')[:90]
            with transaction.atomic():
                comp, was_created = Competency.objects.get_or_create(code=code, defaults={'name': t, 'description': f'Seeded from topic {t}'})
                if was_created:
                    created += 1

        # Create simple mappings
        # Map lessons
        for lesson in Lesson.objects.exclude(topic__exact=''):
            code = lesson.topic.lower().replace(' ', '_')[:90]
            comp = Competency.objects.filter(code=code).first()
            if comp:
                CompetencyMapping.objects.get_or_create(competency=comp, source_type='lesson', source_id=lesson.id, defaults={'weight': 1.0})

        # Map assessments
        for ass in Assessment.objects.exclude(topic__exact=''):
            code = ass.topic.lower().replace(' ', '_')[:90]
            comp = Competency.objects.filter(code=code).first()
            if comp:
                CompetencyMapping.objects.get_or_create(competency=comp, source_type='assessment', source_id=ass.id, defaults={'weight': 1.0})

        self.stdout.write(self.style.SUCCESS(f'Seeding complete. {created} competencies created.'))
