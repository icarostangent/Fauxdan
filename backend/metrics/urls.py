"""
URL Configuration for Django Metrics Application

Provides endpoints for:
- /metrics - Prometheus metrics
- /metrics/health - Health check
- /metrics/status - Metrics status
- /metrics/increment - Increment custom metrics
"""

from django.urls import path
from . import views

app_name = 'metrics'

urlpatterns = [
    # Main Prometheus metrics endpoint
    path('', views.metrics_view, name='prometheus_metrics'),
    
    # Health check endpoint
    path('health/', views.health_check, name='health_check'),
    
    # Metrics status endpoint
    path('status/', views.metrics_status, name='metrics_status'),
    
    # Increment custom metrics endpoint
    path('increment/', views.increment_metric, name='increment_metric'),
    
    # Class-based view for flexible routing
    path('<str:endpoint>/', views.MetricsAPIView.as_view(), name='metrics_api'),
]
