"""
Simple scanner metrics collection for Prometheus
"""
from django.core.management.base import BaseCommand
from internet.models import ScannerJob, JobQueue, JobWorker
from django.utils import timezone
import json


class Command(BaseCommand):
    help = 'Generate scanner metrics for Prometheus'

    def handle(self, *args, **options):
        """Generate Prometheus metrics for scanner service"""
        
        # Job metrics
        job_stats = {}
        for status in ['pending', 'running', 'completed', 'failed', 'timeout']:
            count = ScannerJob.objects.filter(status=status).count()
            job_stats[status] = count
        
        # Worker metrics
        active_workers = JobWorker.objects.filter(status='active').count()
        offline_workers = JobWorker.objects.filter(status='offline').count()
        
        # Queue metrics
        queue_stats = {}
        for queue in JobQueue.objects.all():
            pending = ScannerJob.objects.filter(queue=queue, status='pending').count()
            queue_stats[queue.name] = pending
        
        # Discovery metrics (simplified)
        total_hosts = 0
        total_ports = 0
        for scan in ScannerJob.objects.filter(status='completed'):
            if hasattr(scan, 'scan') and scan.scan:
                total_hosts += scan.scan.hosts.count()
                total_ports += scan.scan.ports.count()
        
        # Generate Prometheus format
        metrics = []
        
        # Job status metrics
        for status, count in job_stats.items():
            metrics.append(f'scanner_jobs_total{{status="{status}"}} {count}')
        
        # Worker metrics
        metrics.append(f'scanner_workers_total{{status="active"}} {active_workers}')
        metrics.append(f'scanner_workers_total{{status="offline"}} {offline_workers}')
        
        # Queue metrics
        for queue_name, pending in queue_stats.items():
            metrics.append(f'scanner_queue_depth{{queue="{queue_name}"}} {pending}')
        
        # Discovery metrics
        metrics.append(f'scanner_hosts_discovered_total {total_hosts}')
        metrics.append(f'scanner_ports_discovered_total {total_ports}')
        
        # Error metrics (simplified)
        error_count = ScannerJob.objects.filter(status='failed').count()
        timeout_count = ScannerJob.objects.filter(status='timeout').count()
        metrics.append(f'scanner_job_errors_total {error_count}')
        metrics.append(f'scanner_timeouts_total {timeout_count}')
        
        # Output metrics
        self.stdout.write('\n'.join(metrics))
