from django.urls import path
from .views import RAGTutorView, SimulatorDebriefView

app_name = 'maritime'

urlpatterns = [
    path('query/', RAGTutorView.as_view(), name='query'),
    path('simulator/<str:run_id>/debrief/', SimulatorDebriefView.as_view(), name='simulator-debrief'),
]
