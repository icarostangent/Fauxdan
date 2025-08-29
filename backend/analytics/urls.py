from django.urls import path
from .views import AnalyticsViewSet, UserStoryDetailView

urlpatterns = [
    path('events/', AnalyticsViewSet.as_view({'post': 'events'}), name='analytics-events'),
    path('dashboard/', AnalyticsViewSet.as_view({'get': 'dashboard'}), name='analytics-dashboard'),
    path('user-story/<uuid:session_id>/view/', UserStoryDetailView.as_view(), name='user_story_detail'),
]
