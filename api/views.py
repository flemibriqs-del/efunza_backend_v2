"""API views module.

This is a minimal stub to replace the [FULL_API_VIEWS_CONTENT] placeholder
so the Django project can import the module and the URLconf can load.
Replace with the real API view implementations as needed.
"""
from rest_framework.views import APIView
from rest_framework.response import Response


class HealthCheckView(APIView):
    def get(self, request):
        return Response({"ok": True})


__all__ = ["HealthCheckView"]
