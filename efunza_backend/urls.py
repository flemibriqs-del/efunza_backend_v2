from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView
from api.views import LoginView

# ============================================================
# ADMIN CONFIGURATION
# ============================================================

admin.site.site_header = "Efunza Administration"
admin.site.site_title = "Efunza Admin"
admin.site.index_title = "Welcome to Efunza Admin Panel"

# ============================================================
# URL PATTERNS
# ============================================================

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/token/', LoginView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('api/', include('api.urls')),
]

# ============================================================
# STATIC & MEDIA FILE SERVING
# ============================================================

# Serve static files (even when DEBUG=False)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Serve media files (user uploads)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    # In production, media files are served by the web server
    # But this ensures they work if needed
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)