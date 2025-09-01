"""
Django Signals for Automatic Metrics Collection

Automatically collects metrics from various Django events and your existing analytics system
"""

from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.core.cache import cache
from django.db import connection
from django.conf import settings
import time

# Import metrics after Django is ready
try:
    from .metrics import (
        analytics_visitors_total, analytics_pageviews_total,
        analytics_sessions_total, analytics_events_total,
        port_scan_results_total, port_scan_duration_seconds,
        celery_tasks_total, celery_task_duration_seconds,
        redis_operations_total
    )
except ImportError:
    # Metrics not available yet
    pass

# Analytics System Integration
@receiver(post_save, sender='analytics.Visitor')
def track_visitor_metrics(sender, instance, created, **kwargs):
    """Track visitor metrics when analytics visitors are created/updated"""
    try:
        if hasattr(instance, 'source'):
            source = instance.source or 'unknown'
        else:
            source = 'unknown'
        
        analytics_visitors_total.labels(source=source).inc()
        
    except (NameError, AttributeError):
        # Metrics not available yet
        pass

@receiver(post_save, sender='analytics.PageView')
def track_pageview_metrics(sender, instance, created, **kwargs):
    """Track pageview metrics when analytics pageviews are created"""
    try:
        if hasattr(instance, 'page'):
            page = instance.page or 'unknown'
        else:
            page = 'unknown'
        
        if hasattr(instance, 'source'):
            source = instance.source or 'unknown'
        else:
            source = 'unknown'
        
        analytics_pageviews_total.labels(page=page, source=source).inc()
        
    except (NameError, AttributeError):
        # Metrics not available yet
        pass

@receiver(post_save, sender='analytics.Session')
def track_session_metrics(sender, instance, created, **kwargs):
    """Track session metrics when analytics sessions are created"""
    try:
        if hasattr(instance, 'source'):
            source = instance.source or 'unknown'
        else:
            source = 'unknown'
        
        analytics_sessions_total.labels(source=source).inc()
        
    except (NameError, AttributeError):
        # Metrics not available yet
        pass

@receiver(post_save, sender='analytics.Event')
def track_event_metrics(sender, instance, created, **kwargs):
    """Track event metrics when analytics events are created"""
    try:
        if hasattr(instance, 'category'):
            category = instance.category or 'unknown'
        else:
            category = 'unknown'
        
        if hasattr(instance, 'action'):
            action = instance.action or 'unknown'
        else:
            action = 'unknown'
        
        analytics_events_total.labels(category=category, action=action).inc()
        
    except (NameError, AttributeError):
        # Metrics not available yet
        pass

# Port Scanning Integration
@receiver(post_save, sender='internet.Host')
def track_host_metrics(sender, instance, created, **kwargs):
    """Track host discovery metrics when new hosts are found"""
    try:
        if created:
            # New host discovered
            port_scan_results_total.labels(
                port='discovery',
                service='host',
                status='new'
            ).inc()
            
    except (NameError, AttributeError):
        # Metrics not available yet
        pass

# Database Query Monitoring
@receiver(pre_save, sender=None)
def track_database_operations(sender, instance, **kwargs):
    """Track database save operations"""
    try:
        if hasattr(instance, '_state') and instance._state.adding:
            # New instance being created
            pass
        else:
            # Existing instance being updated
            pass
            
    except (NameError, AttributeError):
        # Metrics not available yet
        pass

# Cache Operations Monitoring
def track_cache_operation(operation, key, success=True):
    """Track cache operations for metrics"""
    try:
        redis_operations_total.labels(
            operation=operation,
            status='success' if success else 'failure'
        ).inc()
        
    except (NameError, AttributeError):
        # Metrics not available yet
        pass

# Celery Task Monitoring
def track_celery_task(task_name, status, duration=None):
    """Track Celery task execution for metrics"""
    try:
        celery_tasks_total.labels(
            task_name=task_name,
            status=status
        ).inc()
        
        if duration is not None:
            celery_task_duration_seconds.labels(
                task_name=task_name
            ).observe(duration)
            
    except (NameError, AttributeError):
        # Metrics not available yet
        pass

# Custom Metrics Collection
def collect_custom_metrics():
    """Collect custom metrics from your application"""
    try:
        # Example: Collect port scanning metrics from your existing system
        # This would integrate with your port metrics system
        
        # Example: Collect analytics summary metrics
        from django.db.models import Count
        try:
            from analytics.models import Visitor, PageView, Session, Event
            
            # Visitor count by device type (using session data)
            device_counts = Session.objects.values('device_type').annotate(
                count=Count('id')
            )
            for item in device_counts:
                device_type = item['device_type'] or 'unknown'
                analytics_visitors_total.labels(source=device_type).inc(item['count'])
            
            # Page view counts by URL
            pageview_counts = PageView.objects.values('url').annotate(
                count=Count('id')
            )
            for item in pageview_counts:
                url = item['url'] or 'unknown'
                # Extract page name from URL
                if url:
                    page = url.split('/')[-1] if url.split('/')[-1] else 'root'
                else:
                    page = 'unknown'
                analytics_pageviews_total.labels(page=page, source='database').inc(item['count'])
            
            # Session counts by device type
            session_counts = Session.objects.values('device_type').annotate(
                count=Count('id')
            )
            for item in session_counts:
                device_type = item['device_type'] or 'unknown'
                analytics_sessions_total.labels(source=device_type).inc(item['count'])
            
            # Event counts by category and action
            event_counts = Event.objects.values('event_type').annotate(
                count=Count('id')
            )
            for item in event_counts:
                event_type = item['event_type'] or 'unknown'
                analytics_events_total.labels(category='engagement', action=event_type).inc(item['count'])
                
        except ImportError:
            # Analytics models not available
            pass
            
    except Exception:
        # Ignore errors in metrics collection
        pass

# Periodic Metrics Collection
def schedule_metrics_collection():
    """Schedule periodic metrics collection"""
    try:
        from celery import shared_task
        
        @shared_task
        def collect_metrics_task():
            """Celery task to collect metrics periodically"""
            try:
                collect_custom_metrics()
                return "Metrics collected successfully"
            except Exception as e:
                return f"Error collecting metrics: {e}"
        
        # Schedule the task to run every 5 minutes
        # You can adjust this interval based on your needs
        collect_metrics_task.apply_async(countdown=300)  # 5 minutes
        
    except ImportError:
        # Celery not available
        pass
