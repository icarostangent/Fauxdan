from django.core.management.base import BaseCommand
from django.utils import timezone
from internet.models import Port, Host


class Command(BaseCommand):
    help = 'Update timestamps for existing ports and hosts'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without actually doing it'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        current_time = timezone.now()
        
        # Find ports without last_seen
        ports_without_timestamp = Port.objects.filter(last_seen__isnull=True)
        hosts_without_timestamp = Host.objects.filter(last_seen__isnull=True)
        
        if dry_run:
            self.stdout.write(f'Would update {ports_without_timestamp.count()} ports without timestamps')
            self.stdout.write(f'Would update {hosts_without_timestamp.count()} hosts without timestamps')
            
            # Show some examples
            if ports_without_timestamp.exists():
                self.stdout.write('\nExample ports without timestamps:')
                for port in ports_without_timestamp[:5]:
                    self.stdout.write(f'  {port.host.ip}:{port.port_number}/{port.proto}')
            
            if hosts_without_timestamp.exists():
                self.stdout.write('\nExample hosts without timestamps:')
                for host in hosts_without_timestamp[:5]:
                    self.stdout.write(f'  {host.ip}')
        else:
            # Actually update timestamps
            updated_ports = ports_without_timestamp.update(last_seen=current_time)
            updated_hosts = hosts_without_timestamp.update(last_seen=current_time)
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Updated {updated_ports} ports and {updated_hosts} hosts with current timestamp'
                )
            ) 