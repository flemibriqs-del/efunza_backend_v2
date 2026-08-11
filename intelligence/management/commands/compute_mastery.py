from django.core.management.base import BaseCommand
from django.db.models import Avg
from intelligence.models import Competency, CompetencyMapping
from api.models import ItemAttempt, StudentIntelligenceProfile, User

class Command(BaseCommand):
    help = 'Compute simple mastery per user per competency based on ItemAttempt scores and write to StudentIntelligenceProfile.'

    def handle(self, *args, **options):
        users = User.objects.all()
        competencies = Competency.objects.all()

        total_updates = 0

        for user in users:
            profile_data = {}
            weak = []
            recommendations = []
            analytics = {'computed_at_user_id': user.id}

            for comp in competencies:
                mappings = CompetencyMapping.objects.filter(competency=comp)
                source_pairs = [(m.source_type, m.source_id) for m in mappings]

                # Gather attempts linked to assessments mapped to this competency
                attempts = ItemAttempt.objects.filter(user=user, assessment__in=[m.source_id for m in mappings.filter(source_type='assessment')])

                # If no direct assessment mapping, try associated StudentScore topics
                avg_score = None
                if attempts.exists():
                    # average of attempt.score (skip nulls)
                    vals = [a.score for a in attempts if a.score is not None]
                    if vals:
                        avg_score = sum(vals) / len(vals)
                else:
                    # fallback to StudentScore via topic matching (best effort)
                    # Skip for simplicity
                    avg_score = None

                mastery = round(avg_score * 100, 2) if avg_score is not None else None
                profile_data[comp.code] = {'mastery': mastery, 'competency_id': comp.id}

                if mastery is not None and mastery < 70:
                    weak.append({'competency': comp.code, 'mastery': mastery})
                    recommendations.append({'competency': comp.code, 'action': 'Review materials and retry assessments'})

            # Save or update StudentIntelligenceProfile
            sip, _ = StudentIntelligenceProfile.objects.update_or_create(
                user=user,
                defaults={
                    'analytics': analytics,
                    'weak_topics': weak,
                    'recommendations': recommendations,
                    'predictive_performance': {},
                    'career_guidance': {}
                }
            )
            total_updates += 1

        self.stdout.write(self.style.SUCCESS(f'Mastery compute complete. Profiles updated for {total_updates} users.'))
