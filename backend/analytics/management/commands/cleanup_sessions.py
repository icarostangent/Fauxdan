from django.core.management.base import BaseCommand
from django.utils import timezone
from analytics.models import Session
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Clean up old sessions, close timed-out sessions, and calculate durations'

    def add_arguments(self, parser):
        parser.add_argument(
            '--timeout-hours',
            type=int,
            default=24,
            help='Hours of inactivity before a session is considered timed out (default: 24)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without actually doing it'
        )
        parser.add_argument(
            '--force-all',
            action='store_true',
            help='Force close all active sessions and calculate durations'
        )

    def handle(self, *args, **options):
        timeout_hours = options['timeout_hours']
        dry_run = options['dry_run']
        force_all = options['force_all']
        
        cutoff_time = timezone.now() - timedelta(hours=timeout_hours)
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
        
        # Find sessions that need to be closed
        if force_all:
            # Force close all active sessions
            sessions_to_close = Session.objects.filter(end_time__isnull=True)
            self.stdout.write(f'Found {sessions_to_close.count()} active sessions to force close')
        else:
            # Close only timed-out sessions
            sessions_to_close = Session.objects.filter(
                end_time__isnull=True,
                start_time__lt=cutoff_time
            )
            self.stdout.write(f'Found {sessions_to_close.count()} timed-out sessions to close')
        
        # Find sessions with missing durations
        sessions_without_duration = Session.objects.filter(
            end_time__isnot=None,
            duration__isnull=True
        )
        self.stdout.write(f'Found {sessions_without_duration.count()} sessions with missing durations')
        
        if dry_run:
            if sessions_to_close.exists():
                self.stdout.write('\nSessions that would be closed:')
                for session in sessions_to_close[:5]:  # Show first 5
                    self.stdout.write(f'  {session.session_id} (started: {session.start_time})')
                if sessions_to_close.count() > 5:
                    self.stdout.write(f'  ... and {sessions_to_close.count() - 5} more')
            
            if sessions_without_duration.exists():
                self.stdout.write('\nSessions that would have durations calculated:')
                for session in sessions_without_duration[:5]:  # Show first 5
                    self.stdout.write(f'  {session.session_id} (started: {session.start_time}, ended: {session.end_time})')
                if sessions_without_duration.count() > 5:
                    self.stdout.write(f'  ... and {sessions_without_duration.count() - 5} more')
            
            return
        
        # Close timed-out sessions
        closed_count = 0
        for session in sessions_to_close:
            try:
                session.end_time = timezone.now()
                session.duration = session.end_time - session.start_time
                session.save()
                closed_count += 1
                if closed_count % 100 == 0:  # Progress indicator
                    self.stdout.write(f'Closed {closed_count} sessions...')
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error closing session {session.id}: {str(e)}')
                )
        
        # Calculate durations for sessions that are already closed
        duration_count = 0
        for session in sessions_without_duration:
            try:
                session.duration = session.end_time - session.start_time
                session.save()
                duration_count += 1
                if duration_count % 100 == 0:  # Progress indicator
                    self.stdout.write(f'Calculated {duration_count} durations...')
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error calculating duration for session {session.id}: {str(e)}')
                )
        
        # Summary
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully closed {closed_count} sessions and calculated {duration_count} durations'
            )
        )
        
        # Show current stats
        active_sessions = Session.objects.filter(end_time__isnull=True).count()
        total_sessions = Session.objects.count()
        sessions_with_duration = Session.objects.filter(duration__isnot=None).count()
        
        self.stdout.write(f'\nCurrent session statistics:')
        self.stdout.write(f'  Active sessions: {active_sessions}')
        self.stdout.write(f'  Total sessions: {total_sessions}')
        self.stdout.write(f'  Sessions with duration: {sessions_with_duration}')
        self.stdout.write(f'  Sessions without duration: {total_sessions - sessions_with_duration}')
