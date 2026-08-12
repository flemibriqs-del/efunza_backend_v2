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
    # Admin
    path('admin/', admin.site.urls),
    
    # Authentication
    path('api/token/', LoginView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # Core API
    path('api/', include('api.urls')),
    
    # ============================================================
    # INTELLIGENCE ENGINE ROUTES
    # ============================================================
    
    # Intelligence Engine - Main intelligence endpoints
    path('api/intelligence/', include('intelligence.urls')),
    
    # Knowledge Graph - Subject, Topic, Concept management
    path('api/knowledge/', include('knowledge_graph.urls')),
    
    # Evidence & Competency - Evidence tracking and competency assessment
    path('api/evidence/', include('evidence.urls')),
]

# ============================================================
# DEBUG TOOLBAR (Development only)
# ============================================================

if settings.DEBUG:
    try:
        import debug_toolbar
        urlpatterns += [
            path('__debug__/', include(debug_toolbar.urls)),
        ]
    except ImportError:
        pass

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

# ============================================================
# API DOCUMENTATION (Optional)
# ============================================================

# Uncomment if you want to add API documentation
# if settings.DEBUG:
#     from drf_yasg.views import get_schema_view
#     from drf_yasg import openapi
#     from rest_framework import permissions
#     
#     schema_view = get_schema_view(
#         openapi.Info(
#             title="Efunza API",
#             default_version='v1',
#             description="Efunza Learning Platform API",
#             terms_of_service="https://www.efunza.com/terms/",
#             contact=openapi.Contact(email="support@efunza.com"),
#             license=openapi.License(name="BSD License"),
#         ),
#         public=True,
#         permission_classes=(permissions.AllowAny,),
#     )
#     
#     urlpatterns += [
#         path('api/docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
#         path('api/redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
#     ]

# ============================================================
# CATCH-ALL ROUTE FOR SPA (Optional)
# ============================================================

# If you're using a single-page application (React/Vue), 
# add a catch-all route to serve the index.html
# from django.views.generic import TemplateView
# urlpatterns += [
#     path('', TemplateView.as_view(template_name='index.html')),
#     path('<path:path>', TemplateView.as_view(template_name='index.html')),
# ]

# ============================================================
# HEALTH CHECK ENDPOINT
# ============================================================

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def health_check(request):
    """Health check endpoint for monitoring."""
    import sys
    import django
    from datetime import datetime
    
    return JsonResponse({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'environment': settings.ENVIRONMENT,
        'debug': settings.DEBUG,
        'django_version': django.get_version(),
        'python_version': sys.version,
        'apps': {
            'intelligence': 'active',
            'knowledge_graph': 'active',
            'evidence': 'active',
        }
    })

urlpatterns += [
    path('health/', health_check, name='health_check'),
    path('api/health/', health_check, name='api_health_check'),
]

# ============================================================
# ERROR HANDLING
# ============================================================

# Custom error handlers (uncomment if needed)
# handler404 = 'api.views.handler404'
# handler500 = 'api.views.handler500'
# handler403 = 'api.views.handler403'
# handler400 = 'api.views.handler400'

print(f"✅ Efunza URLs loaded | Environment: {settings.ENVIRONMENT}")
print(f"📍 Base URL: {settings.API_PREFIX if hasattr(settings, 'API_PREFIX') else '/api'}")
