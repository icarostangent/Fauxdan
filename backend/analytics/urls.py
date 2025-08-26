from django.urls import path
from .views import AnalyticsViewSet

urlpatterns = [
    path('events/', AnalyticsViewSet.as_view({'post': 'events'}), name='analytics-events'),
    path('dashboard/', AnalyticsViewSet.as_view({'get': 'dashboard'}), name='analytics-dashboard'),
]
