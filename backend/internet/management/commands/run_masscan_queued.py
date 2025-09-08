"""
Management command to queue masscan jobs instead of running them directly
"""
from datetime import datetime
from django.core.management.base import BaseCommand
from internet.lib.queue_service import QueueManager


class Command(BaseCommand):
    help = 'Queue a masscan job for processing by the scanner service'
    
    def __init__(self):
        super().__init__()

    def add_arguments(self, parser):
        parser.add_argument(
            '--target', 
            type=str, 
            required=True,
            help='Target IP address or range'
        )
        parser.add_argument(
            '--ports',
            type=lambda x: [int(p.strip()) for p in x.split(',')],  # Split by comma and convert to int
            default=[],
            help='Comma-separated ports to scan (e.g. "80,443,8080")'
        )
        parser.add_argument(
            '--syn', 
            action='store_true', 
            help='SYN packets'
        )
        parser.add_argument(
            '--tcp', 
            action='store_true', 
            help='TCP packets'
        )
        parser.add_argument(
            '--udp', 
            action='store_true', 
            help='UDP packets'
        )
        parser.add_argument(
            '--use_proxychains', 
            action='store_true', 
            help='Use proxychains'
        )
        parser.add_argument(
            '--rate',
            type=int,
            help='Scan rate in packets per second (e.g. 1000)'
        )
        parser.add_argument(
            '--queue',
            type=str,
            default='default',
            help='Queue name (default: default)'
        )
        parser.add_argument(
            '--priority',
            type=int,
            default=0,
            help='Job priority (higher number = higher priority)'
        )
        parser.add_argument(
            '--schedule',
            type=str,
            help='Schedule for later execution (ISO format: YYYY-MM-DDTHH:MM:SS)'
        )
        parser.add_argument(
            '--user',
            type=int,
            help='User ID to associate with the job'
        )
        parser.add_argument(
            '--timeout',
            type=int,
            default=3600,  # 1 hour default timeout
            help='Maximum scan duration in seconds (default: 3600)'
        )
        parser.add_argument(
            '--resume',
            action='store_true',
            help='Resume paused scan'
        )

    def handle(self, *args, **kwargs):
        target = kwargs['target']
        ports = kwargs['ports']
        syn = kwargs['syn']
        tcp = kwargs['tcp']
        udp = kwargs['udp']
        use_proxychains = kwargs['use_proxychains']
        rate = kwargs['rate']
        queue = kwargs['queue']
        priority = kwargs['priority']
        schedule = kwargs['schedule']
        user_id = kwargs['user']
        timeout = kwargs['timeout']
        resume = kwargs['resume']

        # Build scan options
        scan_options = {}
        if syn:
            scan_options['syn'] = True
        if tcp:
            scan_options['tcp'] = True
        if udp:
            scan_options['udp'] = True
        if use_proxychains:
            scan_options['use_proxychains'] = True
        if rate:
            scan_options['rate'] = rate
        if resume:
            scan_options['resume'] = True
        scan_options['timeout'] = timeout

        # Parse scheduled time
        scheduled_for = None
        if schedule:
            try:
                scheduled_for = datetime.fromisoformat(schedule)
            except ValueError:
                self.stdout.write(
                    self.style.ERROR('Invalid schedule format. Use ISO format (YYYY-MM-DDTHH:MM:SS)')
                )
                return

        # Get user if specified
        user = None
        if user_id:
            from django.contrib.auth.models import User
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'User with ID {user_id} not found')
                )
                return

        # Create the job
        try:
            job = QueueManager.create_job(
                job_type='masscan',
                target=target,
                queue_name=queue,
                ports=ports,
                scan_options=scan_options,
                priority=priority,
                user=user,
                scheduled_for=scheduled_for
            )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully queued masscan job:\n'
                    f'  Job UUID: {job.job_uuid}\n'
                    f'  Target: {target}\n'
                    f'  Ports: {ports if ports else "default"}\n'
                    f'  Queue: {queue}\n'
                    f'  Priority: {priority}\n'
                    f'  Status: {job.status}\n'
                    f'  Scheduled: {scheduled_for or "immediately"}'
                )
            )
            
            # Show how to check status
            self.stdout.write(
                f'\nTo check job status, run:\n'
                f'  python manage.py queue_manager status {job.job_uuid}\n\n'
                f'To list all jobs, run:\n'
                f'  python manage.py queue_manager list'
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Failed to queue job: {str(e)}')
            )
