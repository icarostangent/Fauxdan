"""
Views for Django Metrics Application

Provides endpoints for:
- Prometheus metrics (/metrics)
- Health checks (/health)
- Metrics status (/metrics/status)
"""

from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
from django.conf import settings
from django.db import connection
from django.core.cache import cache
import json
import time
from .metrics import (
    get_metrics, collect_all_metrics,
    http_requests_total, http_request_duration_seconds,
    db_connections_active, cache_hits_total, cache_misses_total,
    analytics_visitors_total, analytics_pageviews_total,
    port_scan_results_total
)

@csrf_exempt
@require_http_methods(["GET"])
def metrics_view(request):
    """
    Prometheus metrics endpoint
    
    Returns all collected metrics in Prometheus format
    """
    try:
        # Collect fresh metrics
        collect_all_metrics()
        
        # Get metrics in Prometheus format
        metrics_data = get_metrics()
        
        return HttpResponse(
            metrics_data,
            content_type='text/plain; version=0.0.4; charset=utf-8'
        )
    except Exception as e:
        # Return error in Prometheus format
        error_metric = f'# ERROR: {str(e)}\n'
        return HttpResponse(
            error_metric,
            content_type='text/plain; version=0.0.4; charset=utf-8',
            status=500
        )

@csrf_exempt
@require_http_methods(["GET"])
def health_check(request):
    """
    Health check endpoint
    
    Returns basic health status of the application
    """
    health_status = {
        'status': 'healthy',
        'timestamp': time.time(),
        'checks': {}
    }
    
    # Check database connectivity
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            health_status['checks']['database'] = 'healthy'
    except Exception as e:
        health_status['checks']['database'] = f'unhealthy: {str(e)}'
        health_status['status'] = 'unhealthy'
    
    # Check cache connectivity
    try:
        cache.set('health_check', 'ok', 1)
        result = cache.get('health_check')
        if result == 'ok':
            health_status['checks']['cache'] = 'healthy'
        else:
            health_status['checks']['cache'] = 'unhealthy: cache not working'
            health_status['status'] = 'unhealthy'
    except Exception as e:
        health_status['checks']['cache'] = f'unhealthy: {str(e)}'
        health_status['status'] = 'unhealthy'
    
    # Check Redis connectivity
    try:
        redis_client = cache.client.get_client()
        redis_client.ping()
        health_status['checks']['redis'] = 'healthy'
    except Exception as e:
        health_status['checks']['redis'] = f'unhealthy: {str(e)}'
        health_status['status'] = 'unhealthy'
    
    # Set appropriate HTTP status
    status_code = 200 if health_status['status'] == 'healthy' else 503
    
    return JsonResponse(health_status, status=status_code)

@csrf_exempt
@require_http_methods(["GET"])
def metrics_status(request):
    """
    Metrics status endpoint
    
    Returns current status of various metrics
    """
    try:
        # Collect fresh metrics
        collect_all_metrics()
        
        # Get current metric values
        status_data = {
            'timestamp': time.time(),
            'metrics': {
                'http_requests': {
                    'total': http_requests_total._value.sum(),
                    'in_progress': http_requests_in_progress._value.sum(),
                },
                'database': {
                    'active_connections': db_connections_active._value.sum(),
                },
                'cache': {
                    'hits': cache_hits_total._value.sum(),
                    'misses': cache_misses_total._value.sum(),
                    'hit_rate': 0.0,
                },
                'analytics': {
                    'visitors': analytics_visitors_total._value.sum(),
                    'pageviews': analytics_pageviews_total._value.sum(),
                },
                'port_scanning': {
                    'results': port_scan_results_total._value.sum(),
                }
            }
        }
        
        # Calculate cache hit rate
        total_cache_ops = status_data['metrics']['cache']['hits'] + status_data['metrics']['cache']['misses']
        if total_cache_ops > 0:
            status_data['metrics']['cache']['hit_rate'] = (
                status_data['metrics']['cache']['hits'] / total_cache_ops
            )
        
        return JsonResponse(status_data)
        
    except Exception as e:
        return JsonResponse(
            {'error': str(e), 'timestamp': time.time()},
            status=500
        )

@csrf_exempt
@require_http_methods(["POST"])
def increment_metric(request):
    """
    Increment custom metrics endpoint
    
    Allows external systems to increment custom metrics
    """
    try:
        data = json.loads(request.body)
        metric_name = data.get('metric')
        value = data.get('value', 1)
        labels = data.get('labels', {})
        
        if not metric_name:
            return JsonResponse(
                {'error': 'metric name is required'},
                status=400
            )
        
        # Find the metric by name
        metric = None
        for attr_name in dir(request):
            if attr_name == metric_name:
                metric = getattr(request, attr_name)
                break
        
        if not metric:
            return JsonResponse(
                {'error': f'metric {metric_name} not found'},
                status=404
            )
        
        # Increment the metric
        if hasattr(metric, 'labels'):
            metric.labels(**labels).inc(value)
        else:
            metric.inc(value)
        
        return JsonResponse({'status': 'success'})
        
    except json.JSONDecodeError:
        return JsonResponse(
            {'error': 'invalid JSON'},
            status=400
        )
    except Exception as e:
        return JsonResponse(
            {'error': str(e)},
            status=500
        )

class MetricsAPIView(View):
    """
    Class-based view for metrics API endpoints
    """
    
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)
    
    def get(self, request, endpoint=None):
        """
        Handle GET requests for different metrics endpoints
        """
        if endpoint == 'health':
            return health_check(request)
        elif endpoint == 'status':
            return metrics_status(request)
        else:
            return metrics_view(request)
    
    def post(self, request, endpoint=None):
        """
        Handle POST requests for metrics endpoints
        """
        if endpoint == 'increment':
            return increment_metric(request)
        else:
            return JsonResponse(
                {'error': 'endpoint not found'},
                status=404
            )
