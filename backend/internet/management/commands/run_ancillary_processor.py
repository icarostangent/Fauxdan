import asyncio
import logging
import signal
import sys
import time
from django.core.management.base import BaseCommand
from django.utils import timezone
from internet.lib.queue_service import QueueService
from internet.models import JobWorker, AncillaryJob
import uuid
import os

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = '[DEPRECATED] Run ancillary job processor to handle banner grabbing, domain enumeration, SSL cert grabbing, and other post-scan tasks. Use run_scanner_service instead for unified job processing.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--max-jobs',
            type=int,
            default=10,
            help='Maximum number of jobs to process in each batch (default: 10)'
        )
        parser.add_argument(
            '--interval',
            type=int,
            default=5,
            help='Interval between job processing cycles in seconds (default: 5)'
        )
        parser.add_argument(
            '--worker-id',
            type=str,
            default=None,
            help='Custom worker ID (default: auto-generated)'
        )

    def handle(self, *args, **options):
        max_jobs = options['max_jobs']
        interval = options['interval']
        worker_id = options['worker_id'] or f"ancillary-processor-{uuid.uuid4().hex[:8]}"
        
        self.stdout.write(
            self.style.SUCCESS(f'Starting ancillary job processor: {worker_id}')
        )
        self.stdout.write(f'Max jobs per batch: {max_jobs}')
        self.stdout.write(f'Processing interval: {interval} seconds')
        
        # Create worker instance
        worker = self.create_worker(worker_id)
        
        # Set up signal handlers
        def signal_handler(signum, frame):
            self.stdout.write(self.style.WARNING('Received shutdown signal'))
            self.cleanup_worker(worker)
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Run the worker
        try:
            self.run_worker(worker, max_jobs, interval)
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING('Worker stopped by user'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Worker error: {e}'))
            logger.error(f'Banner grab worker error: {e}')
        finally:
            self.cleanup_worker(worker)
    
    def create_worker(self, worker_id):
        """Create and register a worker"""
        worker, created = JobWorker.objects.get_or_create(
            worker_id=worker_id,
            defaults={
                'status': 'idle',
                'hostname': os.uname().nodename,
                'pid': os.getpid(),
                'supported_job_types': ['banner_grab', 'domain_enum', 'ssl_cert', 'ancillary'],
                'max_concurrent_jobs': 1,
                'current_job_count': 0,
                'version': '1.0.0',
                'metadata': {
                    'type': 'ancillary_processor',
                    'started_at': timezone.now().isoformat()
                }
            }
        )
        
        if not created:
            # Update existing worker
            worker.status = 'idle'
            worker.hostname = os.uname().nodename
            worker.pid = os.getpid()
            worker.current_job_count = 0
            worker.last_heartbeat = timezone.now()
            worker.metadata.update({
                'type': 'ancillary_processor',
                'restarted_at': timezone.now().isoformat()
            })
            worker.save()
        
        return worker
    
    def run_worker(self, worker, max_jobs, interval):
        """Main worker loop"""
        from asgiref.sync import sync_to_async
        queue_service = QueueService()
        
        self.stdout.write(self.style.SUCCESS('Ancillary job processor started'))
        
        while True:
            try:
                # Update heartbeat
                worker.last_heartbeat = timezone.now()
                worker.save(update_fields=['last_heartbeat'])
                
                # Process ancillary jobs using asyncio.run
                asyncio.run(queue_service.process_ancillary_jobs(max_jobs))
                
                # Wait for next cycle
                time.sleep(interval)
                
            except Exception as e:
                logger.error(f'Error in banner grab worker loop: {e}')
                self.stdout.write(self.style.ERROR(f'Worker loop error: {e}'))
                time.sleep(interval)  # Wait before retrying
    
    def cleanup_worker(self, worker):
        """Clean up worker on shutdown"""
        try:
            worker.status = 'offline'
            worker.current_job_count = 0
            worker.save(update_fields=['status', 'current_job_count'])
            self.stdout.write(self.style.SUCCESS('Worker cleanup completed'))
        except Exception as e:
            logger.error(f'Error during worker cleanup: {e}')


