from rest_framework import serializers
from .models import SimulatorLog, SimulatorDebrief


class SimulatorLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = SimulatorLog
        fields = ['id', 'user', 'run_id', 'timestamp', 'telemetry', 'transcript', 'metadata']
        read_only_fields = ['id', 'timestamp']


class SimulatorDebriefSerializer(serializers.ModelSerializer):
    log = SimulatorLogSerializer(read_only=True)

    class Meta:
        model = SimulatorDebrief
        fields = ['id', 'log', 'generated_at', 'debrief_text', 'issues', 'score', 'metadata']
        read_only_fields = ['id', 'generated_at']
