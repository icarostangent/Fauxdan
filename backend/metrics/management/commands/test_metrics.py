"""
Management command to test Django metrics collection

Usage:
    python manage.py test_metrics
    python manage.py test_metrics --format=json
    python manage.py test_metrics --increment
"""

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.core.cache import cache
from django.db import connection
import json
import time

class Command(BaseCommand):
    help = 'Test Django metrics collection and display current metrics'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--format',
            choices=['text', 'json'],
            default='text',
            help='Output format (default: text)'
        )
        parser.add_argument(
            '--increment',
            action='store_true',
            help='Increment test metrics'
        )
        parser.add_argument(
            '--health',
            action='store_true',
            help='Run health checks'
        )
    
    def handle(self, *args, **options):
        try:
            # Import metrics after Django is ready
            from metrics.metrics import (
                collect_all_metrics, get_metrics,
                http_requests_total, analytics_visitors_total,
                analytics_pageviews_total, port_scan_results_total
            )
            
            # Collect fresh metrics
            self.stdout.write('🔄 Collecting metrics...')
            collect_all_metrics()
            
            # Get metrics data
            metrics_data = get_metrics()
            
            if options['increment']:
                self.increment_test_metrics()
            
            if options['health']:
                self.run_health_checks()
            
            # Display metrics
            if options['format'] == 'json':
                self.display_json_metrics(metrics_data)
            else:
                self.display_text_metrics(metrics_data)
                
        except ImportError as e:
            raise CommandError(f'Could not import metrics: {e}')
        except Exception as e:
            raise CommandError(f'Error testing metrics: {e}')
    
    def increment_test_metrics(self):
        """Increment test metrics for demonstration"""
        try:
            from metrics.metrics import (
                analytics_visitors_total, analytics_pageviews_total,
                port_scan_results_total
            )
            
            # Increment analytics metrics
            analytics_visitors_total.labels(source='test').inc()
            analytics_pageviews_total.labels(page='test_page', source='test').inc()
            analytics_pageviews_total.labels(page='admin', source='test').inc()
            
            # Increment port scan metrics
            port_scan_results_total.labels(port='80', service='http', status='open').inc()
            port_scan_results_total.labels(port='443', service='https', status='open').inc()
            port_scan_results_total.labels(port='22', service='ssh', status='closed').inc()
            
            self.stdout.write(
                self.style.SUCCESS('✅ Test metrics incremented successfully')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'⚠️ Could not increment test metrics: {e}')
            )
    
    def run_health_checks(self):
        """Run basic health checks"""
        self.stdout.write('\n🏥 Running health checks...')
        
        # Database health
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                self.stdout.write(
                    self.style.SUCCESS('✅ Database: Healthy')
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Database: Unhealthy - {e}')
            )
        
        # Cache health
        try:
            cache.set('health_test', 'ok', 1)
            result = cache.get('health_test')
            if result == 'ok':
                self.stdout.write(
                    self.style.SUCCESS('✅ Cache: Healthy')
                )
            else:
                self.stdout.write(
                    self.style.ERROR('❌ Cache: Unhealthy - Not working')
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Cache: Unhealthy - {e}')
            )
        
        # Redis health
        try:
            redis_client = cache.client.get_client()
            redis_client.ping()
            self.stdout.write(
                self.style.SUCCESS('✅ Redis: Healthy')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Redis: Unhealthy - {e}')
            )
    
    def display_text_metrics(self, metrics_data):
        """Display metrics in human-readable text format"""
        self.stdout.write('\n📊 Current Django Metrics:')
        self.stdout.write('=' * 50)
        
        # Parse and display key metrics
        lines = metrics_data.decode('utf-8').split('\n')
        
        # Group metrics by type
        http_metrics = []
        db_metrics = []
        cache_metrics = []
        analytics_metrics = []
        port_metrics = []
        other_metrics = []
        
        for line in lines:
            if line.startswith('django_http_'):
                http_metrics.append(line)
            elif line.startswith('django_db_'):
                db_metrics.append(line)
            elif line.startswith('django_cache_'):
                cache_metrics.append(line)
            elif line.startswith('django_analytics_'):
                analytics_metrics.append(line)
            elif line.startswith('django_port_scan_'):
                port_metrics.append(line)
            elif line and not line.startswith('#'):
                other_metrics.append(line)
        
        # Display grouped metrics
        if http_metrics:
            self.stdout.write('\n🌐 HTTP Request Metrics:')
            for metric in http_metrics[:5]:  # Show first 5
                self.stdout.write(f'  {metric}')
        
        if db_metrics:
            self.stdout.write('\n🗄️ Database Metrics:')
            for metric in db_metrics[:5]:
                self.stdout.write(f'  {metric}')
        
        if cache_metrics:
            self.stdout.write('\n💾 Cache Metrics:')
            for metric in cache_metrics[:5]:
                self.stdout.write(f'  {metric}')
        
        if analytics_metrics:
            self.stdout.write('\n📈 Analytics Metrics:')
            for metric in analytics_metrics[:5]:
                self.stdout.write(f'  {metric}')
        
        if port_metrics:
            self.stdout.write('\n🔍 Port Scanning Metrics:')
            for metric in port_metrics[:5]:
                self.stdout.write(f'  {metric}')
        
        if other_metrics:
            self.stdout.write('\n🔧 Other Metrics:')
            for metric in other_metrics[:10]:
                self.stdout.write(f'  {metric}')
        
        self.stdout.write('\n' + '=' * 50)
        self.stdout.write(
            self.style.SUCCESS('✅ Metrics collection completed successfully!')
        )
    
    def display_json_metrics(self, metrics_data):
        """Display metrics in JSON format"""
        try:
            # Parse metrics into structured format
            lines = metrics_data.decode('utf-8').split('\n')
            metrics_dict = {}
            
            for line in lines:
                if line and not line.startswith('#'):
                    if ' ' in line:
                        metric_name, value = line.rsplit(' ', 1)
                        metrics_dict[metric_name] = value
            
            # Output as JSON
            output = {
                'timestamp': time.time(),
                'metrics': metrics_dict,
                'total_metrics': len(metrics_dict)
            }
            
            self.stdout.write(json.dumps(output, indent=2))
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error formatting JSON: {e}')
            )
