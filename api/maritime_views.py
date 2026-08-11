# api/maritime_views.py
import hashlib
from django.utils import timezone
from django.db import IntegrityError
from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from api.maritime_models import MaritimeCourse, MaritimeEnrollment, MaritimeContent
from api.maritime_serializers import (
    MaritimeCourseSerializer, MaritimeEnrollmentSerializer, MaritimeContentSerializer,
)


class MaritimeCourseViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = MaritimeCourse.objects.all()
    serializer_class = MaritimeCourseSerializer
    permission_classes = [permissions.AllowAny]
    filterset_fields = ["track"]
    ordering_fields = ["order", "created_at", "title"]
    ordering = ["track", "order"]

    @action(detail=False, methods=["get"], permission_classes=[permissions.AllowAny])
    def by_track(self, request):
        track = request.query_params.get("track")
        if not track:
            return Response({"error": "track parameter required"}, status=400)
        courses = self.queryset.filter(track=track)
        serializer = self.get_serializer(courses, many=True)
        return Response(serializer.data)


class MaritimeEnrollmentViewSet(viewsets.ModelViewSet):
    serializer_class = MaritimeEnrollmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    ordering_fields = ["enrolled_at", "status"]
    ordering = ["-enrolled_at"]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return MaritimeEnrollment.objects.all()
        return MaritimeEnrollment.objects.filter(user=user)

    def create(self, request, *args, **kwargs):
        """
        Override create to validate and gracefully handle duplicate race conditions
        (unique user+course). If an IntegrityError occurs, return the existing enrollment.
        """
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        try:
            self.perform_create(serializer)
        except IntegrityError:
            # Race condition fallback: return existing enrollment if present
            user = request.user
            course_id = request.data.get('course')
            existing = MaritimeEnrollment.objects.filter(user=user, course_id=course_id).first()
            if existing:
                existing_ser = self.get_serializer(existing)
                return Response(existing_ser.data, status=status.HTTP_200_OK)
            # If not found, return a generic error
            return Response({"detail": "Enrollment already exists or could not be created."}, status=status.HTTP_400_BAD_REQUEST)

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        serializer.save()

    @action(detail=True, methods=["post"], permission_classes=[IsAdminUser])
    def confirm_payment(self, request, pk=None):
        """
        Admin endpoint to confirm an enrollment payment.
        This generates and emails a one-time access code and sets status to awaiting_activation.
        """
        enrollment = self.get_object()
        enrollment.confirm_payment(confirmed_by_user=request.user)
        return Response(self.get_serializer(enrollment).data)

    @action(detail=False, methods=["post"], permission_classes=[permissions.IsAuthenticated])
    def claim_code(self, request):
        """
        Redeem a one-time access code. POST body: { "access_code": "CODE" }
        """
        code = (request.data.get('access_code') or '').strip()
        if not code:
            return Response({"detail": "access_code is required"}, status=status.HTTP_400_BAD_REQUEST)

        code_hash = hashlib.sha256(code.encode('utf-8')).hexdigest()

        try:
            enrollment = MaritimeEnrollment.objects.get(access_code_hash=code_hash)
        except MaritimeEnrollment.DoesNotExist:
            return Response({"detail": "Invalid access code"}, status=status.HTTP_404_NOT_FOUND)

        # expiry
        if enrollment.access_code_expires_at and timezone.now() > enrollment.access_code_expires_at:
            return Response({"detail": "Access code expired"}, status=status.HTTP_400_BAD_REQUEST)

        if enrollment.access_code_used:
            return Response({"detail": "This access code has already been used"}, status=status.HTTP_400_BAD_REQUEST)

        if enrollment.user != request.user:
            return Response({"detail": "This access code does not belong to your account"}, status=status.HTTP_403_FORBIDDEN)

        # mark used & activate
        enrollment.access_code_used = True
        enrollment.mark_activated()
        enrollment.save(update_fields=['access_code_used', 'status'])
        return Response(self.get_serializer(enrollment).data)


class MaritimeContentViewSet(viewsets.ModelViewSet):
    queryset = MaritimeContent.objects.all()
    serializer_class = MaritimeContentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filterset_fields = ["course", "content_type", "is_published"]
    ordering_fields = ["order", "created_at"]
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    search_fields = ["title", "body", "external_url"]

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.is_staff:
            return qs
        return qs.filter(is_published=True)

    def perform_create(self, serializer):
        serializer.save()