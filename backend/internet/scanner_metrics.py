"""
Scanner metrics endpoint for Prometheus
"""
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods
from internet.metrics.scanner_metrics import metrics_collector
import logging

logger = logging.getLogger(__name__)


@require_http_methods(["GET"])
def scanner_metrics(request):
    """
    Prometheus metrics endpoint for scanner service
    """
    try:
        # Update metrics with current data
        from internet.models import ScannerJob, JobQueue, JobWorker
        
        # Update job metrics
        for job in ScannerJob.objects.all():
            metrics_collector.update_job_metrics(job)
        
        # Update worker metrics
        for worker in JobWorker.objects.all():
            metrics_collector.update_worker_metrics(worker)
        
        # Update queue metrics
        for queue in JobQueue.objects.all():
            metrics_collector.update_queue_metrics(queue)
        
        # Get metrics in Prometheus format
        metrics_data = metrics_collector.get_metrics()
        
        return HttpResponse(metrics_data, content_type='text/plain; version=0.0.4; charset=utf-8')
        
    except Exception as e:
        logger.error(f"Error generating scanner metrics: {e}")
        return HttpResponse(f"Error generating metrics: {e}", status=500)
