from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.shortcuts import get_object_or_404
from django.db import transaction

from .serializers import SimulatorLogSerializer, SimulatorDebriefSerializer
from .models import SimulatorLog, SimulatorDebrief
from .ai import generate_rag_answer, generate_debrief


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

        serializer = SimulatorDebriefSerializer(debrief_obj)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
