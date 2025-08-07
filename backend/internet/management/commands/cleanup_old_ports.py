from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from internet.models import Port, Host


class Command(BaseCommand):
    help = 'Clean up old ports and update timestamps'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Number of days to consider a port "old" (default: 30)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without actually doing it'
        )

    def handle(self, *args, **options):
        days = options['days']
        dry_run = options['dry_run']
        
        cutoff_date = timezone.now() - timedelta(days=days)
        
        # Find old ports
        old_ports = Port.objects.filter(last_seen__lt=cutoff_date)
        old_hosts = Host.objects.filter(last_seen__lt=cutoff_date)
        
        if dry_run:
            self.stdout.write(f'Would remove {old_ports.count()} old ports (older than {days} days)')
            
            # Show some examples
            if old_ports.exists():
                self.stdout.write('\nExample old ports:')
                for port in old_ports[:5]:
                    self.stdout.write(f'  {port.host.ip}:{port.port_number}/{port.proto} (last seen: {port.last_seen})')
            
            if old_hosts.exists():
                self.stdout.write('\nExample old hosts:')
                for host in old_hosts[:5]:
                    self.stdout.write(f'  {host.ip} (last seen: {host.last_seen})')
        else:
            # Actually remove old data
            old_ports_count = old_ports.count()
            old_hosts_count = old_hosts.count()
            
            old_ports.delete()
            old_hosts.delete()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Removed {old_ports_count} old ports and {old_hosts_count} old hosts'
                )
            ) 