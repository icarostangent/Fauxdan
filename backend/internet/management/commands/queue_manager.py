"""
Management command for queue operations
"""
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from internet.lib.queue_service import QueueManager
from internet.models import ScannerJob, JobQueue, JobWorker


class Command(BaseCommand):
    help = 'Manage scanner job queues'
    
    def add_arguments(self, parser):
        subparsers = parser.add_subparsers(dest='action', help='Available actions')
        
        # Create job command
        create_parser = subparsers.add_parser('create', help='Create a new scanner job')
        create_parser.add_argument('--type', required=True, choices=['masscan', 'nmap', 'custom'], help='Job type')
        create_parser.add_argument('--target', required=True, help='Target IP, range, or hostname')
        create_parser.add_argument('--ports', nargs='+', type=int, help='Ports to scan')
        create_parser.add_argument('--queue', default='default', help='Queue name')
        create_parser.add_argument('--priority', type=int, default=0, help='Job priority')
        create_parser.add_argument('--user', type=int, help='User ID')
        create_parser.add_argument('--schedule', help='Schedule for later (ISO format)')
        create_parser.add_argument('--syn', action='store_true', help='Use SYN scan')
        create_parser.add_argument('--tcp', action='store_true', help='Use TCP scan')
        create_parser.add_argument('--udp', action='store_true', help='Use UDP scan')
        create_parser.add_argument('--rate', type=int, help='Scan rate')
        create_parser.add_argument('--proxychains', action='store_true', help='Use proxychains')
        create_parser.add_argument('--timeout', type=int, default=3600, help='Maximum scan duration in seconds (default: 3600)')
        
        # List jobs command
        list_parser = subparsers.add_parser('list', help='List jobs')
        list_parser.add_argument('--status', choices=['pending', 'running', 'completed', 'failed', 'cancelled'])
        list_parser.add_argument('--queue', help='Filter by queue')
        list_parser.add_argument('--limit', type=int, default=50, help='Limit results')
        
        # Status command
        status_parser = subparsers.add_parser('status', help='Get job status')
        status_parser.add_argument('job_uuid', help='Job UUID')
        
        # Cancel command
        cancel_parser = subparsers.add_parser('cancel', help='Cancel a job')
        cancel_parser.add_argument('job_uuid', help='Job UUID')
        
        # Stats command
        stats_parser = subparsers.add_parser('stats', help='Show queue statistics')
        stats_parser.add_argument('--queue', help='Specific queue name')
        
        # Workers command
        workers_parser = subparsers.add_parser('workers', help='Show worker status')
        
        # Cleanup command
        cleanup_parser = subparsers.add_parser('cleanup', help='Clean up old jobs')
        cleanup_parser.add_argument('--days', type=int, default=7, help='Days to keep completed jobs')
        cleanup_parser.add_argument('--dry-run', action='store_true', help='Show what would be deleted')
    
    def handle(self, *args, **options):
        action = options['action']
        
        if action == 'create':
            self._create_job(options)
        elif action == 'list':
            self._list_jobs(options)
        elif action == 'status':
            self._show_status(options)
        elif action == 'cancel':
            self._cancel_job(options)
        elif action == 'stats':
            self._show_stats(options)
        elif action == 'workers':
            self._show_workers()
        elif action == 'cleanup':
            self._cleanup_jobs(options)
        else:
            self.stdout.write(self.style.ERROR('No action specified'))
    
    def _create_job(self, options):
        """Create a new scanner job"""
        # Parse scan options
        scan_options = {}
        if options.get('syn'):
            scan_options['syn'] = True
        if options.get('tcp'):
            scan_options['tcp'] = True
        if options.get('udp'):
            scan_options['udp'] = True
        if options.get('rate'):
            scan_options['rate'] = options['rate']
        if options.get('proxychains'):
            scan_options['use_proxychains'] = True
        if options.get('timeout'):
            scan_options['timeout'] = options['timeout']
        
        # Parse scheduled time
        scheduled_for = None
        if options.get('schedule'):
            try:
                scheduled_for = datetime.fromisoformat(options['schedule'])
            except ValueError:
                self.stdout.write(self.style.ERROR('Invalid schedule format. Use ISO format (YYYY-MM-DDTHH:MM:SS)'))
                return
        
        # Get user
        user = None
        if options.get('user'):
            from django.contrib.auth.models import User
            try:
                user = User.objects.get(id=options['user'])
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'User with ID {options["user"]} not found'))
                return
        
        # Create job
        job = QueueManager.create_job(
            job_type=options['type'],
            target=options['target'],
            queue_name=options['queue'],
            ports=options.get('ports'),
            scan_options=scan_options,
            priority=options['priority'],
            user=user,
            scheduled_for=scheduled_for
        )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Created job {job.job_uuid}\n'
                f'Type: {job.job_type}\n'
                f'Target: {job.target}\n'
                f'Queue: {job.queue.name}\n'
                f'Status: {job.status}'
            )
        )
    
    def _list_jobs(self, options):
        """List jobs with optional filtering"""
        queryset = ScannerJob.objects.all()
        
        if options.get('status'):
            queryset = queryset.filter(status=options['status'])
        
        if options.get('queue'):
            queryset = queryset.filter(queue__name=options['queue'])
        
        jobs = queryset.order_by('-created_at')[:options['limit']]
        
        if not jobs:
            self.stdout.write('No jobs found')
            return
        
        self.stdout.write(f"{'UUID':<36} {'Type':<10} {'Target':<20} {'Status':<12} {'Created':<20}")
        self.stdout.write('-' * 100)
        
        for job in jobs:
            created_str = job.created_at.strftime('%Y-%m-%d %H:%M:%S')
            self.stdout.write(
                f"{str(job.job_uuid):<36} {job.job_type:<10} {job.target:<20} {job.status:<12} {created_str:<20}"
            )
    
    def _show_status(self, options):
        """Show job status"""
        job_uuid = options['job_uuid']
        status = QueueManager.get_job_status(job_uuid)
        
        if not status:
            self.stdout.write(self.style.ERROR(f'Job {job_uuid} not found'))
            return
        
        self.stdout.write(f"Job UUID: {status['job_uuid']}")
        self.stdout.write(f"Status: {status['status']}")
        self.stdout.write(f"Progress: {status['progress']}%")
        self.stdout.write(f"Target: {status['target']}")
        self.stdout.write(f"Type: {status['job_type']}")
        self.stdout.write(f"Created: {status['created_at']}")
        
        if status['started_at']:
            self.stdout.write(f"Started: {status['started_at']}")
        if status['completed_at']:
            self.stdout.write(f"Completed: {status['completed_at']}")
        if status['error_message']:
            self.stdout.write(f"Error: {status['error_message']}")
    
    def _cancel_job(self, options):
        """Cancel a job"""
        job_uuid = options['job_uuid']
        success = QueueManager.cancel_job(job_uuid)
        
        if success:
            self.stdout.write(self.style.SUCCESS(f'Job {job_uuid} cancelled'))
        else:
            self.stdout.write(self.style.ERROR(f'Could not cancel job {job_uuid}'))
    
    def _show_stats(self, options):
        """Show queue statistics"""
        stats = QueueManager.get_queue_stats(options.get('queue'))
        
        if not stats:
            self.stdout.write('No queues found')
            return
        
        for queue_name, queue_stats in stats.items():
            self.stdout.write(f"\nQueue: {queue_name}")
            self.stdout.write(f"  Enabled: {queue_stats['enabled']}")
            self.stdout.write(f"  Max concurrent: {queue_stats['max_concurrent_jobs']}")
            self.stdout.write(f"  Pending: {queue_stats['pending_jobs']}")
            self.stdout.write(f"  Running: {queue_stats['running_jobs']}")
            self.stdout.write(f"  Completed: {queue_stats['completed_jobs']}")
            self.stdout.write(f"  Failed: {queue_stats['failed_jobs']}")
    
    def _show_workers(self):
        """Show worker status"""
        workers = JobWorker.objects.all().order_by('-last_heartbeat')
        
        if not workers:
            self.stdout.write('No workers found')
            return
        
        self.stdout.write(f"{'Worker ID':<30} {'Status':<10} {'Hostname':<20} {'Jobs':<5} {'Last Heartbeat':<20}")
        self.stdout.write('-' * 90)
        
        for worker in workers:
            last_heartbeat = worker.last_heartbeat.strftime('%Y-%m-%d %H:%M:%S')
            self.stdout.write(
                f"{worker.worker_id:<30} {worker.status:<10} {worker.hostname:<20} {worker.current_job_count:<5} {last_heartbeat:<20}"
            )
    
    def _cleanup_jobs(self, options):
        """Clean up old completed jobs"""
        days = options['days']
        cutoff_date = timezone.now() - timedelta(days=days)
        dry_run = options.get('dry_run', False)
        
        # Find old completed jobs
        old_jobs = ScannerJob.objects.filter(
            status__in=['completed', 'failed', 'cancelled'],
            completed_at__lt=cutoff_date
        )
        
        count = old_jobs.count()
        
        if count == 0:
            self.stdout.write('No old jobs to clean up')
            return
        
        if dry_run:
            self.stdout.write(f'Would delete {count} jobs completed before {cutoff_date}')
            return
        
        # Delete old jobs
        deleted_count, _ = old_jobs.delete()
        self.stdout.write(self.style.SUCCESS(f'Deleted {deleted_count} old jobs'))
