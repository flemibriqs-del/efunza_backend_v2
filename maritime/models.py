from django.db import models
from django.conf import settings

class SimulatorLog(models.Model):
    """Raw simulator run data saved for debriefing and analysis"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='simulator_logs')
    run_id = models.CharField(max_length=200, db_index=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    telemetry = models.JSONField(default=dict, blank=True)
    transcript = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"SimulatorLog {self.run_id} ({self.user or 'anonymous'})"


class SimulatorDebrief(models.Model):
    """Generated debrief for a simulator run"""
    log = models.ForeignKey(SimulatorLog, on_delete=models.CASCADE, related_name='debriefs')
    generated_at = models.DateTimeField(auto_now_add=True)
    debrief_text = models.TextField()
    issues = models.JSONField(default=list, blank=True)
    score = models.FloatField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-generated_at']

    def __str__(self):
        return f"Debrief for {self.log.run_id} @ {self.generated_at.isoformat()}"
