# api/maritime_models.py
import hashlib
from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.core.mail import send_mail
from django.conf import settings


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class MaritimeCourse(TimeStampedModel):
    TRACK_CHOICES = (
        ('deck', 'Deck Officer'),
        ('engine', 'Engine Officer'),
        ('rating', 'Rating'),
        ('general', 'General Maritime'),
    )

    code = models.CharField(max_length=20, unique=True)
    title = models.CharField(max_length=255)
    credits = models.PositiveIntegerField(default=3)
    duration_weeks = models.PositiveIntegerField(default=12)
    summary = models.TextField(blank=True)
    outcomes = models.JSONField(default=list, blank=True)
    track = models.CharField(max_length=20, choices=TRACK_CHOICES, default='general')
    order = models.PositiveIntegerField(default=0)
    fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    class Meta:
        ordering = ['track', 'order', 'code']

    def __str__(self):
        return f"{self.code} - {self.title}"


class MaritimeEnrollment(TimeStampedModel):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('pending_verification', 'Pending verification'),
        ('awaiting_activation', 'Awaiting activation'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='maritime_enrollments')
    course = models.ForeignKey(MaritimeCourse, on_delete=models.CASCADE, related_name='enrollments')
    track = models.CharField(max_length=20, choices=MaritimeCourse.TRACK_CHOICES, default='general')
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='pending')
    enrolled_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    payment_phone = models.CharField(max_length=32, blank=True)
    transaction_code = models.CharField(max_length=128, blank=True)
    payment_status = models.CharField(max_length=32, default='unpaid')
    payment_confirmed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='confirmed_enrollments')
    payment_confirmed_at = models.DateTimeField(null=True, blank=True)

    # access code storage (hashed)
    access_code = models.CharField(max_length=64, blank=True, help_text="LEGACY plaintext (optional)")
    access_code_hash = models.CharField(max_length=64, blank=True, db_index=True)
    access_code_expires_at = models.DateTimeField(null=True, blank=True)
    access_code_sent = models.BooleanField(default=False)
    access_code_used = models.BooleanField(default=False)

    class Meta:
        unique_together = ('user', 'course')
        ordering = ['-enrolled_at']

    def __str__(self):
        return f"{self.user.username} - {self.course.code} ({self.status})"

    def _hash_code(self, plaintext: str) -> str:
        return hashlib.sha256(plaintext.encode('utf-8')).hexdigest()

    def generate_access_code(self, length=16, expires_days=7):
        for _ in range(10):
            raw = get_random_string(length).upper()
            raw_hash = self._hash_code(raw)
            if not self.__class__.objects.filter(access_code_hash=raw_hash).exists():
                self.access_code_hash = raw_hash
                if expires_days:
                    self.access_code_expires_at = timezone.now() + timezone.timedelta(days=expires_days)
                self.access_code_used = False
                self.access_code = raw  # optional temporary storage for backfill
                self.save(update_fields=['access_code_hash', 'access_code_expires_at', 'access_code_used', 'access_code'])
                return raw
        raise RuntimeError("Could not generate unique access code")

    def confirm_payment(self, confirmed_by_user=None, code_length=16, expires_days=7):
        self.payment_status = 'paid'
        self.payment_confirmed_by = confirmed_by_user
        self.payment_confirmed_at = timezone.now()

        code_plain = self.generate_access_code(length=code_length, expires_days=expires_days)
        self.status = 'awaiting_activation'
        self.save()

        try:
            subject = f"Efunza Maritime Academy — Access code for {self.course.title}"
            expiry_str = self.access_code_expires_at.strftime('%Y-%m-%d %H:%M UTC') if self.access_code_expires_at else 'N/A'
            body = (
                f"Hello {self.user.get_full_name() or self.user.username},\n\n"
                f"Your payment has been confirmed. Use the following one-time code to activate the course:\n\n"
                f"{code_plain}\n\n"
                f"This code expires on {expiry_str} and can be used only once.\n\n"
                "Regards,\nEfunza Team"
            )
            from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@efunza.local')
            send_mail(subject, body, from_email, [self.user.email], fail_silently=True)
            self.access_code_sent = True
            self.save(update_fields=['access_code_sent'])
        except Exception:
            pass

    def mark_activated(self):
        self.status = 'confirmed'
        self.access_code_used = True
        self.save(update_fields=['status', 'access_code_used'])


class MaritimeContent(TimeStampedModel):
    CONTENT_TYPES = (
        ('text', 'Text / HTML'),
        ('video', 'Video URL'),
        ('file', 'File upload'),
        ('link', 'External Link'),
    )

    course = models.ForeignKey(MaritimeCourse, on_delete=models.CASCADE, related_name='contents')
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, blank=True)
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPES, default='text')
    body = models.TextField(blank=True, help_text='Use for text or HTML content')
    file = models.FileField(upload_to='maritime_contents/', null=True, blank=True)
    external_url = models.URLField(blank=True)
    order = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=True)

    class Meta:
        ordering = ['order', 'created_at']
        unique_together = ('course', 'slug')
        indexes = [
            models.Index(fields=['course', 'order']),
        ]

    def __str__(self):
        return f"{self.course.code} - {self.title}"

    def _generate_unique_slug(self):
        base = slugify(self.title) or 'content'
        slug = base
        counter = 1
        qs = self.__class__.objects.filter(course=self.course)
        if self.pk:
            qs = qs.exclude(pk=self.pk)
        while qs.filter(slug=slug).exists():
            slug = f"{base}-{counter}"
            counter += 1
        return slug

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self._generate_unique_slug()
        if self.content_type == 'file' and not self.file:
            self.is_published = False
        if self.content_type == 'link' and not self.external_url:
            self.is_published = False
        super().save(*args, **kwargs)