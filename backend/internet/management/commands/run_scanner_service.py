"""
Management command to run the scanner service worker
"""
import asyncio
import os
import signal
import sys
from django.core.management.base import BaseCommand
from internet.lib.queue_service import QueueService


class Command(BaseCommand):
    help = 'Run the scanner service worker'
    
    def __init__(self):
        super().__init__()
        self.queue_service = None
        self.shutdown_requested = False
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--job-types',
            nargs='+',
            default=['masscan', 'nmap', 'custom'],
            help='Supported job types (default: masscan nmap custom)'
        )
        parser.add_argument(
            '--max-concurrent',
            type=int,
            default=1,
            help='Maximum concurrent jobs (default: 1)'
        )
        parser.add_argument(
            '--worker-id',
            type=str,
            help='Custom worker ID (default: auto-generated)'
        )
    
    def handle(self, *args, **options):
        job_types = options['job_types']
        max_concurrent = options['max_concurrent']
        worker_id = options.get('worker_id')
        
        if worker_id:
            # Override the worker ID if provided
            self.queue_service = QueueService()
            self.queue_service.worker_id = worker_id
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Starting scanner service worker...\n'
                f'Job types: {", ".join(job_types)}\n'
                f'Max concurrent jobs: {max_concurrent}'
            )
        )
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        try:
            # Run the async queue service
            asyncio.run(self._run_service(job_types, max_concurrent))
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING('Received interrupt signal'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Service error: {e}'))
            sys.exit(1)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.stdout.write(self.style.WARNING(f'Received signal {signum}, shutting down...'))
        self.shutdown_requested = True
        if self.queue_service:
            self.queue_service.running = False
    
    async def _run_service(self, job_types, max_concurrent):
        """Run the queue service"""
        if not self.queue_service:
            self.queue_service = QueueService()
        
        # Override worker ID if provided
        if hasattr(self, 'worker_id'):
            self.queue_service.worker_id = self.worker_id
        
        try:
            await self.queue_service.start_worker(job_types, max_concurrent)
        except asyncio.CancelledError:
            self.stdout.write(self.style.WARNING('Service cancelled'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Service error: {e}'))
            raise
