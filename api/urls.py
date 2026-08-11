from django.urls import path, include
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from .views import *
from .maritime_views import (
    MaritimeCourseViewSet,
    MaritimeEnrollmentViewSet,
    MaritimeContentViewSet,
)

# ============================================================
# MAIN ROUTER
# ============================================================

router = DefaultRouter()
router.register('programs', ProgramViewSet, basename='program')
router.register('enrollments', EnrollmentViewSet, basename='enrollment')
router.register('lessons', LessonViewSet, basename='lesson')
router.register('videos', VideoViewSet, basename='video')
router.register('content', ContentItemViewSet, basename='content')
router.register('assessments', AssessmentViewSet, basename='assessment')
router.register('student-scores', StudentScoreViewSet, basename='student-score')
router.register('student-intelligence/profiles', StudentIntelligenceViewSet, basename='student-intelligence-profile')
router.register('activity-logs', ActivityLogViewSet, basename='activity-log')
router.register('tasks', TaskViewSet, basename='task')
router.register('notes', NoteViewSet, basename='note')
router.register('discussions', DiscussionViewSet, basename='discussion')
router.register('assignments', AssignmentViewSet, basename='assignment')
router.register('grades', GradeViewSet, basename='grade')
router.register('events', EventViewSet, basename='event')
router.register('study-groups', StudyGroupViewSet, basename='study-group')
router.register('career-sessions', CareerSessionViewSet, basename='career-session')
router.register('feedback', FeedbackViewSet, basename='feedback')
router.register('support/contact', SupportRequestViewSet, basename='support-contact')
router.register('books', BookViewSet, basename='book')
router.register('my-books', MyBookViewSet, basename='my-book')
router.register('achievements', AchievementViewSet, basename='achievement')
router.register('notifications', NotificationViewSet, basename='notification')
router.register('subscriptions', SubscriptionViewSet, basename='subscription')
router.register('lab-projects', LabProjectViewSet, basename='lab-project')
router.register('school-os', SchoolOSResourceViewSet, basename='school-os')
router.register('starter-school', StarterSchoolViewSet, basename='starter-school')
router.register('boarding-pro', BoardingProViewSet, basename='boarding-pro')
router.register('smart-boarding-plus', SmartBoardingPlusViewSet, basename='smart-boarding-plus')
router.register('readathon/reports', ReadathonReportViewSet, basename='readathon-report')
router.register('readathon/interventions', InterventionNoteViewSet, basename='readathon-intervention')

# ============================================================
# 🚢 MARITIME ACADEMY ROUTER
# ============================================================
router.register('maritime-courses', MaritimeCourseViewSet, basename='maritime-course')
router.register('maritime-enrollments', MaritimeEnrollmentViewSet, basename='maritime-enrollment')
router.register('maritime-contents', MaritimeContentViewSet, basename='maritime-content')

# ============================================================
# 🛒 STORE ROUTER
# ============================================================
store_router = DefaultRouter()
store_router.register('products', ProductViewSet, basename='product')
store_router.register('categories', CategoryViewSet, basename='category')
store_router.register('orders', OrderViewSet, basename='order')
store_router.register('reviews', ProductReviewViewSet, basename='product-review')
store_router.register('payments', PaymentViewSet, basename='payment')
store_router.register('addresses', AddressViewSet, basename='address')
store_router.register('coupons', CouponViewSet, basename='coupon')

# ============================================================
# URL PATTERNS
# ============================================================
urlpatterns = [
    path('favicon.ico', RedirectView.as_view(url='/static/favicon.ico', permanent=True)),
    path('', api_root, name='api-root'),
    path('health/', health, name='health'),

    # Authentication
    path('auth/register/', RegisterView.as_view(), name='auth-register'),
    path('auth/login/', LoginView.as_view(), name='auth-login'),
    path('auth/change-password/', ChangePasswordView.as_view(), name='auth-change-password'),
    path('auth/forgot-password/', PasswordResetRequestView.as_view(), name='auth-forgot-password'),
    path('auth/password-reset/', PasswordResetRequestView.as_view(), name='auth-password-reset'),
    path('auth/reset-password/', PasswordResetConfirmView.as_view(), name='auth-reset-password'),
    path('auth/password-reset-confirm/', PasswordResetConfirmView.as_view(), name='auth-password-reset-confirm'),
    path('auth/privacy-settings/', PrivacySettingsView.as_view(), name='auth-privacy-settings'),
    path('me/', MeView.as_view(), name='me'),

    # AI chat, mpesa, etc.
    path('ai/chat/', AIChatView.as_view(), name='ai-chat'),
    path('mpesa/initiate/', MpesaInitiateView.as_view(), name='mpesa-initiate'),
    path('mpesa/status/<str:order_number>/', mpesa_status, name='mpesa-status'),

    # other custom endpoints...
    path('', include(router.urls)),
    path('store/', include(store_router.urls)),
]

# AI E-Lab extra routes
from django.urls import path as _path, include as _include
urlpatterns += [_path("", _include("api.elab_ai_urls"))]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)