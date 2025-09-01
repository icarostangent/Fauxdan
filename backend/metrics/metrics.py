"""
Django Prometheus Metrics Collection

This module provides Prometheus metrics for Django applications including:
- HTTP request metrics (count, duration, status codes)
- Database query metrics
- Custom business metrics
- System health metrics
"""

from prometheus_client import (
    Counter, Histogram, Gauge, Summary, 
    generate_latest, CONTENT_TYPE_LATEST,
    REGISTRY
)
from prometheus_client.core import CollectorRegistry
import time
import threading
from django.conf import settings
from django.db import connection
from django.core.cache import cache
import redis

# Create a separate registry for Django metrics
django_registry = CollectorRegistry()

# HTTP Request Metrics
http_requests_total = Counter(
    'django_http_requests_total',
    'Total number of HTTP requests',
    ['method', 'endpoint', 'status'],
    registry=django_registry
)

http_request_duration_seconds = Histogram(
    'django_http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
    registry=django_registry
)

http_requests_in_progress = Gauge(
    'django_http_requests_in_progress',
    'Number of HTTP requests currently in progress',
    ['method', 'endpoint'],
    registry=django_registry
)

# Database Metrics
db_query_duration_seconds = Histogram(
    'django_db_query_duration_seconds',
    'Database query duration in seconds',
    ['database', 'operation'],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5],
    registry=django_registry
)

db_connections_active = Gauge(
    'django_db_connections_active',
    'Number of active database connections',
    ['database'],
    registry=django_registry
)

db_connections_idle = Gauge(
    'django_db_connections_idle',
    'Number of idle database connections',
    ['database'],
    registry=django_registry
)

# Cache Metrics
cache_hits_total = Counter(
    'django_cache_hits_total',
    'Total number of cache hits',
    ['cache_backend'],
    registry=django_registry
)

cache_misses_total = Counter(
    'django_cache_misses_total',
    'Total number of cache misses',
    ['cache_backend'],
    registry=django_registry
)

cache_operations_total = Counter(
    'django_cache_operations_total',
    'Total number of cache operations',
    ['cache_backend', 'operation'],
    registry=django_registry
)

# Business Metrics (from your existing analytics)
analytics_visitors_total = Counter(
    'django_analytics_visitors_total',
    'Total number of unique visitors',
    ['source'],
    registry=django_registry
)

analytics_pageviews_total = Counter(
    'django_analytics_pageviews_total',
    'Total number of page views',
    ['page', 'source'],
    registry=django_registry
)

analytics_sessions_total = Counter(
    'django_analytics_sessions_total',
    'Total number of user sessions',
    ['source'],
    registry=django_registry
)

analytics_events_total = Counter(
    'django_analytics_events_total',
    'Total number of analytics events',
    ['category', 'action'],
    registry=django_registry
)

# Port Scanning Metrics (from your port metrics system)
port_scan_results_total = Counter(
    'django_port_scan_results_total',
    'Total number of port scan results',
    ['port', 'service', 'status'],
    registry=django_registry
)

port_scan_duration_seconds = Histogram(
    'django_port_scan_duration_seconds',
    'Port scan duration in seconds',
    ['target_type'],
    buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0],
    registry=django_registry
)

# System Health Metrics
django_app_info = Gauge(
    'django_app_info',
    'Django application information',
    ['version', 'environment'],
    registry=django_registry
)

celery_tasks_total = Counter(
    'django_celery_tasks_total',
    'Total number of Celery tasks',
    ['task_name', 'status'],
    registry=django_registry
)

celery_task_duration_seconds = Histogram(
    'django_celery_task_duration_seconds',
    'Celery task duration in seconds',
    ['task_name'],
    buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0],
    registry=django_registry
)

# Redis Metrics
redis_connections_active = Gauge(
    'django_redis_connections_active',
    'Number of active Redis connections',
    registry=django_registry
)

redis_operations_total = Counter(
    'django_redis_operations_total',
    'Total number of Redis operations',
    ['operation', 'status'],
    registry=django_registry
)

# Initialize app info metric
def init_app_info():
    """Initialize application information metrics"""
    try:
        from django import get_version
        django_version = get_version()
    except ImportError:
        django_version = "unknown"
    
    environment = getattr(settings, 'DJANGO_ENV', 'development')
    django_app_info.labels(
        version=django_version,
        environment=environment
    ).set(1)

# Database connection monitoring
def update_db_metrics():
    """Update database connection metrics"""
    try:
        if hasattr(connection, 'connection'):
            conn = connection.connection
            if hasattr(conn, 'pool'):
                # For connection pooling
                pool = conn.pool
                db_connections_active.labels(database='default').set(
                    getattr(pool, 'size', 0)
                )
                db_connections_idle.labels(database='default').set(
                    getattr(pool, 'idle', 0)
                )
            else:
                # For single connections
                db_connections_active.labels(database='default').set(1)
                db_connections_idle.labels(database='default').set(0)
    except Exception:
        # If we can't get connection info, set to 0
        db_connections_active.labels(database='default').set(0)
        db_connections_idle.labels(database='default').set(0)

# Cache monitoring
def update_cache_metrics():
    """Update cache performance metrics"""
    try:
        # Test cache operations
        test_key = '_metrics_test_key'
        test_value = 'test_value'
        
        # Test set operation
        cache.set(test_key, test_value, 1)
        cache_operations_total.labels(
            cache_backend='default',
            operation='set'
        ).inc()
        
        # Test get operation
        result = cache.get(test_key)
        if result == test_value:
            cache_hits_total.labels(cache_backend='default').inc()
            cache_operations_total.labels(
                cache_backend='default',
                operation='get'
            ).inc()
        else:
            cache_misses_total.labels(cache_backend='default').inc()
            cache_operations_total.labels(
                cache_backend='default',
                operation='get'
            ).inc()
            
        # Clean up test key
        cache.delete(test_key)
        
    except Exception:
        # Cache might not be available
        pass

# Redis monitoring
def update_redis_metrics():
    """Update Redis connection metrics"""
    try:
        # Get Redis connection info
        redis_client = cache.client.get_client()
        if hasattr(redis_client, 'connection_pool'):
            pool = redis_client.connection_pool
            redis_connections_active.set(
                getattr(pool, '_created_connections', 0)
            )
    except Exception:
        # Redis might not be available
        redis_connections_active.set(0)

# Metrics collection function
def collect_all_metrics():
    """Collect all metrics and update them"""
    update_db_metrics()
    update_cache_metrics()
    update_redis_metrics()
    
    # Import and call custom metrics collection
    try:
        from .signals import collect_custom_metrics
        collect_custom_metrics()
    except ImportError:
        # Signals not available yet
        pass

# Initialize metrics on module import
init_app_info()

# Thread-local storage for request timing
_request_timing = threading.local()

class MetricsMiddleware:
    """
    Django middleware for collecting HTTP request metrics
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        # Start timing
        start_time = time.time()
        
        # Increment in-progress requests
        endpoint = self._get_endpoint(request.path)
        http_requests_in_progress.labels(
            method=request.method,
            endpoint=endpoint
        ).inc()
        
        # Process request
        response = self.get_response(request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Record metrics
        http_requests_total.labels(
            method=request.method,
            endpoint=endpoint,
            status=response.status_code
        ).inc()
        
        http_request_duration_seconds.labels(
            method=request.method,
            endpoint=endpoint
        ).observe(duration)
        
        # Decrement in-progress requests
        http_requests_in_progress.labels(
            method=request.method,
            endpoint=endpoint
        ).dec()
        
        return response
    
    def _get_endpoint(self, path):
        """Extract endpoint name from path"""
        # Remove leading slash and limit length
        endpoint = path.lstrip('/')[:50]
        if not endpoint:
            endpoint = 'root'
        return endpoint

class DatabaseMetricsMiddleware:
    """
    Django middleware for collecting database metrics
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        # Get initial query count
        initial_queries = len(connection.queries)
        initial_time = time.time()
        
        # Process request
        response = self.get_response(request)
        
        # Calculate metrics
        final_queries = len(connection.queries)
        final_time = time.time()
        
        query_count = final_queries - initial_queries
        total_time = final_time - initial_time
        
        if query_count > 0:
            # Record query duration
            db_query_duration_seconds.labels(
                database='default',
                operation='request'
            ).observe(total_time)
        
        return response

def get_metrics():
    """Get all metrics in Prometheus format"""
    # Update metrics before returning
    collect_all_metrics()
    
    # Return metrics in Prometheus format
    return generate_latest(django_registry)

# Export metrics for easy access
__all__ = [
    'http_requests_total',
    'http_request_duration_seconds',
    'http_requests_in_progress',
    'db_query_duration_seconds',
    'db_connections_active',
    'db_connections_idle',
    'cache_hits_total',
    'cache_misses_total',
    'cache_operations_total',
    'analytics_visitors_total',
    'analytics_pageviews_total',
    'analytics_sessions_total',
    'analytics_events_total',
    'port_scan_results_total',
    'port_scan_duration_seconds',
    'django_app_info',
    'celery_tasks_total',
    'celery_task_duration_seconds',
    'redis_connections_active',
    'redis_operations_total',
    'MetricsMiddleware',
    'DatabaseMetricsMiddleware',
    'get_metrics',
    'collect_all_metrics',
]
