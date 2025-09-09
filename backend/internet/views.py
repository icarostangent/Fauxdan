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
        from django.core.paginator import Paginator
        from django.db.models import Q
        
        query = request.GET.get('q', '')
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 50))
        
        if not query:
            return Response({'error': 'Query parameter "q" is required'}, status=400)
        
        # Search hosts by IP address, domain names, port numbers, or banners
        hosts = Host.objects.filter(
            Q(ip__icontains=query) | 
            Q(domains__name__icontains=query) |
            Q(ports__port_number__icontains=query) |
            Q(ports__banner__icontains=query)
        ).distinct().prefetch_related('ports', 'domains', 'ssl_certificates')
        
        # Paginate results
        paginator = Paginator(hosts, page_size)
        page_obj = paginator.get_page(page)
        
        # Serialize the results
        serializer = HostSerializer(page_obj.object_list, many=True)
        
        return Response({
            'count': paginator.count,
            'next': page_obj.next_page_number() if page_obj.has_next() else None,
            'previous': page_obj.previous_page_number() if page_obj.has_previous() else None,
            'page': page,
            'page_size': page_size,
            'total_pages': paginator.num_pages,
            'results': serializer.data
        })


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
        from internet.models import ScannerJob, AncillaryJob, JobQueue, JobWorker, Scan, Host, Port
        from django.utils import timezone
        from datetime import timedelta
        
        now = timezone.now()
        one_hour_ago = now - timedelta(hours=1)
        
        # Job metrics with labels (ScannerJob)
        job_stats = {}
        for status in ['pending', 'queued', 'running', 'completed', 'failed', 'cancelled', 'retrying']:
            count = ScannerJob.objects.filter(status=status).count()
            job_stats[status] = count
            
        # Ancillary job metrics
        ancillary_job_stats = {}
        for status in ['pending', 'queued', 'running', 'completed', 'failed', 'cancelled', 'retrying']:
            count = AncillaryJob.objects.filter(status=status).count()
            ancillary_job_stats[status] = count
        
        # Worker metrics
        active_workers = JobWorker.objects.filter(status='active').count()
        offline_workers = JobWorker.objects.filter(status='offline').count()
        
        # Queue metrics - get actual pending jobs per queue
        queue_stats = {}
        for queue in JobQueue.objects.all():
            pending = ScannerJob.objects.filter(queue=queue, status='pending').count()
            queue_stats[queue.name] = pending
            
        # Ancillary jobs don't have queues, so we'll track total pending
        ancillary_pending_total = AncillaryJob.objects.filter(status='pending').count()
        
        # Real-time discovery metrics (last hour)
        recent_hosts = Host.objects.filter(last_seen__gte=one_hour_ago).count()
        recent_ports = Port.objects.filter(last_seen__gte=one_hour_ago).count()
        
        # Running jobs with progress
        running_jobs = ScannerJob.objects.filter(status='running')
        running_count = running_jobs.count()
        
        # Error metrics (last hour)
        recent_errors = ScannerJob.objects.filter(
            status='failed', 
            completed_at__gte=one_hour_ago
        ).count()
        recent_cancelled = ScannerJob.objects.filter(
            status='cancelled', 
            completed_at__gte=one_hour_ago
        ).count()
        
        # Ancillary job error metrics (last hour)
        recent_ancillary_errors = AncillaryJob.objects.filter(
            status='failed',
            completed_at__gte=one_hour_ago
        ).count()
        recent_ancillary_cancelled = AncillaryJob.objects.filter(
            status='cancelled',
            completed_at__gte=one_hour_ago
        ).count()
        
        # Generate Prometheus format
        metrics = []
        
        # Job status metrics with proper labels
        for status, count in job_stats.items():
            metrics.append(f'scanner_jobs_total{{status="{status}"}} {count}')
            
        # Ancillary job status metrics
        for status, count in ancillary_job_stats.items():
            metrics.append(f'scanner_ancillary_jobs_total{{status="{status}"}} {count}')
        
        # Worker metrics
        metrics.append(f'scanner_workers_total{{status="active"}} {active_workers}')
        metrics.append(f'scanner_workers_total{{status="offline"}} {offline_workers}')
        
        # Queue depth metrics
        for queue_name, pending in queue_stats.items():
            metrics.append(f'scanner_queue_depth{{queue="{queue_name}"}} {pending}')
            
        # Ancillary job pending count (no queues for ancillary jobs)
        metrics.append(f'scanner_ancillary_jobs_pending_total {ancillary_pending_total}')
        
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
        metrics.append(f'scanner_job_cancelled_total {recent_cancelled}')
        metrics.append(f'scanner_ancillary_job_errors_total {recent_ancillary_errors}')
        metrics.append(f'scanner_ancillary_job_cancelled_total {recent_ancillary_cancelled}')
        
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