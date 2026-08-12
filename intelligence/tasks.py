from celery import shared_task
import logging
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def update_all_mastery_task(self, batch_size: int = 100) -> dict:
    """Celery task to update mastery scores for all student profiles.

    This will iterate over StudentIntelligenceProfile rows and call the
    MasteryEngine.update_all_mastery() method for each profile's intelligence
    engine. The task is intentionally defensive: exceptions for an individual
    profile are logged and skipped so a single bad profile does not stop the
    whole job.

    Args:
        batch_size: number of profiles to process per run (keeps memory bounded)

    Returns:
        Summary dict with counts and optional per-profile results.
    """
    try:
        from intelligence.models import StudentIntelligenceProfile
        from intelligence.services.intelligence_service import IntelligenceService
    except Exception as e:
        logger.exception("Failed to import intelligence models/services: %s", e)
        raise

    results = {}
    processed = 0

    qs = StudentIntelligenceProfile.objects.all().iterator()
    for profile in qs:
        if processed and processed % batch_size == 0:
            # allow the worker to update heartbeat
            logger.info("Processed %d profiles, continuing...", processed)

        try:
            svc = IntelligenceService(profile.user)
            res = svc.mastery_engine.update_all_mastery()
            results[str(profile.id)] = res
        except Exception as exc:
            logger.exception("Error updating mastery for profile %s: %s", profile.id, exc)
            results[str(profile.id)] = {'error': str(exc)}
        processed += 1

    return {
        'processed_profiles': processed,
        'results_count': len(results),
        'completed_at': timezone.now().isoformat(),
    }


@shared_task
def process_pending_evidence(batch_limit: int = 100) -> dict:
    """Process or auto-verify pending competency evidence.

    This task scans for evidence in 'submitted' state and performs simple
    automated processing such as auto-verifying high-quality items. It's a
    conservative starter implementation — replace or extend with your
    production verification pipeline.
    """
    try:
        from evidence.models import CompetencyEvidence
        from evidence.engines.competency_engine import CompetencyEngine
    except Exception as e:
        logger.exception("Failed to import evidence models/engines: %s", e)
        raise

    pending = CompetencyEvidence.objects.filter(status='submitted').order_by('created_at')[:batch_limit]
    processed = []
    errors = {}

    for ev in pending:
        try:
            engine = CompetencyEngine(ev.user)

            # Example auto-verify rule: quality_score >= 80 and not expired
            if ev.quality_score is not None and ev.quality_score >= 80 and ev.is_valid():
                # Use engine.verify_evidence to perform verification side-effects
                engine.verify_evidence(evidence_id=str(ev.id), verifier=ev.user, notes='Auto-verified by batch task')
                processed.append(str(ev.id))
            else:
                # Keep as submitted for manual review / separate worker
                logger.debug("Skipping evidence %s (quality=%s)", ev.id, ev.quality_score)

        except Exception as exc:
            logger.exception("Error processing evidence %s: %s", ev.id, exc)
            errors[str(ev.id)] = str(exc)

    return {
        'processed': len(processed),
        'processed_ids': processed,
        'errors_count': len(errors),
        'errors': errors,
        'completed_at': timezone.now().isoformat(),
    }


# Backwards-compatible task names expected by settings.py (aliasing)
@shared_task(name='intelligence.tasks.update_all_mastery')
def update_all_mastery(*args, **kwargs):
    return update_all_mastery_task.apply(args=args, kwargs=kwargs).get()


@shared_task(name='intelligence.tasks.process_pending_evidence')
def process_pending_evidence_task(*args, **kwargs):
    return process_pending_evidence.apply(args=args, kwargs=kwargs).get()
