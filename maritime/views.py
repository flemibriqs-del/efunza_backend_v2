from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.shortcuts import get_object_or_404
from django.db import transaction
import logging

from .serializers import SimulatorLogSerializer, SimulatorDebriefSerializer
from .models import SimulatorLog, SimulatorDebrief
from .ai import generate_rag_answer, generate_debrief

logger = logging.getLogger(__name__)


class RAGTutorView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        query = request.data.get('query')
        if not query:
            return Response({'detail': 'query is required'}, status=status.HTTP_400_BAD_REQUEST)

        result = generate_rag_answer(query)
        return Response(result)


class SimulatorDebriefView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, run_id, *args, **kwargs):
        payload = request.data
        telemetry = payload.get('telemetry', {})
        transcript = payload.get('transcript', '')

        # Save the simulator log and generated debrief transactionally
        with transaction.atomic():
            log = SimulatorLog.objects.create(
                user=request.user if request.user.is_authenticated else None,
                run_id=run_id,
                telemetry=telemetry,
                transcript=transcript,
                metadata=payload.get('metadata', {}),
            )

            debrief = generate_debrief(telemetry, transcript)

            debrief_obj = SimulatorDebrief.objects.create(
                log=log,
                debrief_text=debrief.get('debrief_text', ''),
                issues=debrief.get('issues', []),
                score=debrief.get('score'),
                metadata={'sources': debrief.get('sources', [])},
            )

            # Also create an Evidence row in intelligence_core if available so
            # simulator activity contributes to the mastery engine.
            try:
                from intelligence_core.models import StudentIntelligenceProfile, Evidence

                # Only include safe, minimal payload fields to avoid leaking PII.
                safe_payload = {}
                md = payload.get('metadata') or {}
                if isinstance(md, dict):
                    if 'topic' in md:
                        safe_payload['topic'] = md['topic']
                    if 'difficulty' in md:
                        safe_payload['difficulty'] = md['difficulty']
                    if 'concept_ids' in md:
                        safe_payload['concept_ids'] = md['concept_ids']

                if debrief.get('score') is not None:
                    safe_payload['score'] = debrief.get('score')

                # Associate evidence with the user's intelligence profile if present
                if request.user and request.user.is_authenticated:
                    profile, _ = StudentIntelligenceProfile.objects.get_or_create(user=request.user)
                    Evidence.objects.create(
                        profile=profile,
                        source_type='simulator',
                        source_id=str(log.id) if hasattr(log, 'id') else run_id,
                        activity_type='simulator_debrief',
                        payload=safe_payload,
                        confidence=debrief.get('score'),
                    )
            except Exception as exc:
                # Do not fail the request if intelligence_core is missing or an error occurs
                logger.debug('Could not create Intelligence Evidence: %s', exc)

        serializer = SimulatorDebriefSerializer(debrief_obj)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
