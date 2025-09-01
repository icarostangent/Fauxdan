#!/usr/bin/env python
"""
Script to generate test metrics data for Django dashboard testing
"""

import os
import sys
import django
from django.conf import settings

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from metrics.metrics import (
    analytics_visitors_total,
    analytics_pageviews_total,
    analytics_sessions_total,
    analytics_events_total,
    port_scan_results_total,
    port_scan_duration_seconds
)

def generate_test_metrics():
    """Generate test metrics data"""
    print("Generating test metrics data...")
    
    # Generate analytics metrics
    sources = ['organic', 'direct', 'referral', 'social']
    pages = ['home', 'hosts', 'blog', 'api', 'admin']
    
    for source in sources:
        # Generate visitor metrics
        for i in range(5, 15):
            analytics_visitors_total.labels(source=source).inc()
        
        # Generate pageview metrics
        for page in pages:
            for i in range(10, 30):
                analytics_pageviews_total.labels(page=page, source=source).inc()
        
        # Generate session metrics
        for i in range(3, 8):
            analytics_sessions_total.labels(source=source).inc()
    
    # Generate event metrics
    categories = ['navigation', 'search', 'interaction']
    actions = ['click', 'view', 'submit']
    
    for category in categories:
        for action in actions:
            for i in range(5, 20):
                analytics_events_total.labels(category=category, action=action).inc()
    
    # Generate port scan metrics
    ports = [80, 443, 22, 3306, 5432, 6379, 27017]
    services = ['http', 'https', 'ssh', 'mysql', 'postgresql', 'redis', 'mongodb']
    statuses = ['open', 'closed', 'filtered']
    
    for port, service in zip(ports, services):
        for status in statuses:
            for i in range(10, 50):
                port_scan_results_total.labels(port=str(port), service=service, status=status).inc()
    
    # Generate port scan duration metrics
    target_types = ['subnet', 'single', 'range']
    for target_type in target_types:
        for i in range(5, 15):
            port_scan_duration_seconds.labels(target_type=target_type).observe(i * 0.5)
    
    print("Test metrics generated successfully!")
    print("Metrics have been incremented. Check Prometheus for current values.")

if __name__ == '__main__':
    generate_test_metrics()
