"""
Views for the internet app
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from .models import Scan, Host, Domain, Port, Proxy, DNSRelay
from .serializers import (
    ScanSerializer, HostSerializer, DomainSerializer, PortSerializer, 
    ProxySerializer, DNSRelaySerializer
)
# from .lib.search import UniversalSearch
import logging

logger = logging.getLogger(__name__)


class ScanViewSet(viewsets.ModelViewSet):
    queryset = Scan.objects.all()
    serializer_class = ScanSerializer
    
    @action(detail=True, methods=['post'])
    def start_scan(self, request, pk=None):
        scan = self.get_object()
        # Add scan start logic here
        return Response({'status': 'scan started'})
    
    @action(detail=True, methods=['post'])
    def stop_scan(self, request, pk=None):
        scan = self.get_object()
        # Add scan stop logic here
        return Response({'status': 'scan stopped'})


class HostViewSet(viewsets.ModelViewSet):
    queryset = Host.objects.all()
    serializer_class = HostSerializer


class DomainViewSet(viewsets.ModelViewSet):
    queryset = Domain.objects.all()
    serializer_class = DomainSerializer


class PortViewSet(viewsets.ModelViewSet):
    queryset = Port.objects.all()
    serializer_class = PortSerializer


class ProxyViewSet(viewsets.ModelViewSet):
    queryset = Proxy.objects.all()
    serializer_class = ProxySerializer


class DNSRelayViewSet(viewsets.ModelViewSet):
    queryset = DNSRelay.objects.all()
    serializer_class = DNSRelaySerializer


class UniversalSearchView(APIView):
    def get(self, request):
        query = request.GET.get('q', '')
        if not query:
            return Response({'error': 'Query parameter "q" is required'}, status=400)
        
        # Simple search implementation
        results = {'query': query, 'results': []}
        return Response(results)


class CreateScanView(APIView):
    def post(self, request):
        # Add scan creation logic here
        return Response({'message': 'Scan creation endpoint'}, status=200)


class HealthCheckView(APIView):
    def get(self, request):
        return JsonResponse({
            'status': 'healthy',
            'timestamp': timezone.now().isoformat(),
            'service': 'fauxdan-backend'
        })


@require_http_methods(["GET"])
def scanner_metrics(request):
    """
    Scanner metrics endpoint for Prometheus with real-time data
    """
    try:
        from internet.models import ScannerJob, JobQueue, JobWorker, Scan, Host, Port
        from django.utils import timezone
        from datetime import timedelta
        
        now = timezone.now()
        one_hour_ago = now - timedelta(hours=1)
        
        # Job metrics with labels
        job_stats = {}
        for status in ['pending', 'running', 'completed', 'failed', 'timeout']:
            count = ScannerJob.objects.filter(status=status).count()
            job_stats[status] = count
        
        # Worker metrics
        active_workers = JobWorker.objects.filter(status='active').count()
        offline_workers = JobWorker.objects.filter(status='offline').count()
        
        # Queue metrics - get actual pending jobs per queue
        queue_stats = {}
        for queue in JobQueue.objects.all():
            pending = ScannerJob.objects.filter(queue=queue, status='pending').count()
            queue_stats[queue.name] = pending
        
        # Real-time discovery metrics (last hour)
        recent_hosts = Host.objects.filter(created_at__gte=one_hour_ago).count()
        recent_ports = Port.objects.filter(created_at__gte=one_hour_ago).count()
        
        # Running jobs with progress
        running_jobs = ScannerJob.objects.filter(status='running')
        running_count = running_jobs.count()
        
        # Error metrics (last hour)
        recent_errors = ScannerJob.objects.filter(
            status='failed', 
            updated_at__gte=one_hour_ago
        ).count()
        recent_timeouts = ScannerJob.objects.filter(
            status='timeout', 
            updated_at__gte=one_hour_ago
        ).count()
        
        # Generate Prometheus format
        metrics = []
        
        # Job status metrics with proper labels
        for status, count in job_stats.items():
            metrics.append(f'scanner_jobs_total{{status="{status}"}} {count}')
        
        # Worker metrics
        metrics.append(f'scanner_workers_total{{status="active"}} {active_workers}')
        metrics.append(f'scanner_workers_total{{status="offline"}} {offline_workers}')
        
        # Queue depth metrics
        for queue_name, pending in queue_stats.items():
            metrics.append(f'scanner_queue_depth{{queue="{queue_name}"}} {pending}')
        
        # Discovery metrics (total and recent)
        total_hosts = Host.objects.count()
        total_ports = Port.objects.count()
        metrics.append(f'scanner_hosts_discovered_total {total_hosts}')
        metrics.append(f'scanner_ports_discovered_total {total_ports}')
        
        # Recent discovery rates (for rate calculations)
        metrics.append(f'scanner_hosts_discovered_recent {recent_hosts}')
        metrics.append(f'scanner_ports_discovered_recent {recent_ports}')
        
        # Error metrics
        metrics.append(f'scanner_job_errors_total {recent_errors}')
        metrics.append(f'scanner_timeouts_total {recent_timeouts}')
        
        # Running job progress
        for job in running_jobs:
            progress = getattr(job, 'progress', 0)
            metrics.append(f'scanner_job_progress{{job_uuid="{job.job_uuid}",target="{job.target}"}} {progress}')
        
        # Add some sample data for testing
        if running_count > 0:
            # Simulate some discovery activity for running jobs
            metrics.append(f'scanner_discovery_rate_simulation 1.5')
            metrics.append(f'scanner_packet_rate_simulation 750.0')
        
        # Output metrics
        metrics_text = '\n'.join(metrics)
        return HttpResponse(metrics_text, content_type='text/plain; version=0.0.4; charset=utf-8')
        
    except Exception as e:
        logger.error(f"Error generating scanner metrics: {e}")
        return HttpResponse(f"Error generating metrics: {e}", status=500)