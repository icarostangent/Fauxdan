"""
Admin Configuration for Django Metrics Application

Provides admin interface for monitoring metrics collection
"""

from django.contrib import admin
from django.http import HttpResponse
from django.urls import path
from django.utils.html import format_html
from .metrics import collect_all_metrics, get_metrics
from .views import health_check, metrics_status
import json

@admin.register(admin.models.LogEntry)
class MetricsAdmin(admin.ModelAdmin):
    """
    Admin interface for metrics monitoring
    """
    
    change_list_template = 'admin/metrics_change_list.html'
    
    def get_urls(self):
        """Add custom URLs for metrics endpoints"""
        urls = super().get_urls()
        custom_urls = [
            path('metrics/', self.admin_site.admin_view(self.metrics_view), name='metrics_view'),
            path('health/', self.admin_site.admin_view(self.health_view), name='health_view'),
            path('status/', self.admin_site.admin_view(self.status_view), name='status_view'),
        ]
        return custom_urls + urls
    
    def metrics_view(self, request):
        """Display Prometheus metrics in admin"""
        try:
            collect_all_metrics()
            metrics_data = get_metrics()
            
            # Format metrics for display
            formatted_metrics = []
            for line in metrics_data.decode('utf-8').split('\n'):
                if line and not line.startswith('#'):
                    formatted_metrics.append(line)
            
            content = format_html(
                '<h2>Django Prometheus Metrics</h2>'
                '<p>Current metrics collection:</p>'
                '<pre style="background: #f5f5f5; padding: 10px; overflow-x: auto;">{}</pre>',
                '\n'.join(formatted_metrics[:100])  # Show first 100 lines
            )
            
            return HttpResponse(content)
            
        except Exception as e:
            return HttpResponse(f'Error collecting metrics: {str(e)}', status=500)
    
    def health_view(self, request):
        """Display health check results in admin"""
        try:
            response = health_check(request)
            health_data = json.loads(response.content.decode('utf-8'))
            
            # Format health status
            status_color = 'green' if health_data['status'] == 'healthy' else 'red'
            content = format_html(
                '<h2>Application Health Status</h2>'
                '<p>Status: <span style="color: {}; font-weight: bold;">{}</span></p>'
                '<h3>Component Health:</h3>',
                status_color, health_data['status']
            )
            
            for component, status in health_data['checks'].items():
                component_color = 'green' if 'healthy' in status else 'red'
                content += format_html(
                    '<p><strong>{}:</strong> <span style="color: {};">{}</span></p>',
                    component.title(), component_color, status
                )
            
            return HttpResponse(content)
            
        except Exception as e:
            return HttpResponse(f'Error checking health: {str(e)}', status=500)
    
    def status_view(self, request):
        """Display metrics status in admin"""
        try:
            response = metrics_status(request)
            status_data = json.loads(response.content.decode('utf-8'))
            
            # Format metrics status
            content = format_html(
                '<h2>Metrics Status</h2>'
                '<p>Last updated: {}</p>'
                '<h3>Current Metrics:</h3>',
                status_data['timestamp']
            )
            
            for category, metrics in status_data['metrics'].items():
                content += format_html('<h4>{}:</h4>', category.title())
                if isinstance(metrics, dict):
                    for metric, value in metrics.items():
                        if isinstance(value, float):
                            content += format_html('<p><strong>{}:</strong> {:.2f}</p>', metric, value)
                        else:
                            content += format_html('<p><strong>{}:</strong> {}</p>', metric, value)
                else:
                    content += format_html('<p>{}</p>', metrics)
            
            return HttpResponse(content)
            
        except Exception as e:
            return HttpResponse(f'Error getting status: {str(e)}', status=500)
    
    def changelist_view(self, request, extra_context=None):
        """Custom changelist view with metrics links"""
        extra_context = extra_context or {}
        extra_context.update({
            'metrics_links': [
                {
                    'name': 'View Metrics',
                    'url': 'metrics/',
                    'description': 'View current Prometheus metrics'
                },
                {
                    'name': 'Health Check',
                    'url': 'health/',
                    'description': 'Check application health status'
                },
                {
                    'name': 'Metrics Status',
                    'url': 'status/',
                    'description': 'View current metrics status'
                },
            ]
        })
        return super().changelist_view(request, extra_context)
