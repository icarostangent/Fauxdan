from django.core.management.base import BaseCommand
from django.utils import timezone
from internet.models import Host, Port, Scan
from asgiref.sync import sync_to_async
import asyncio


class Command(BaseCommand):
    help = 'Test timestamp functionality'

    def handle(self, *args, **options):
        self.stdout.write('Testing timestamp functionality...')
        
        # Create a test scan
        scan = Scan.objects.create(
            scan_command='test',
            scan_type='test'
        )
        
        # Test host timestamp update
        host, created = Host.objects.get_or_create(ip='192.168.1.100')
        if created:
            self.stdout.write(f'Created new host: {host.ip}')
        else:
            self.stdout.write(f'Found existing host: {host.ip}')
        
        # Update host timestamp
        old_time = host.last_seen
        host.last_seen = timezone.now()
        host.save()
        self.stdout.write(f'Updated host timestamp: {old_time} -> {host.last_seen}')
        
        # Test port timestamp update
        port, created = Port.objects.get_or_create(
            host=host,
            port_number=80,
            proto='tcp',
            defaults={
                'status': 'open',
                'scan': scan,
                'last_seen': timezone.now()
            }
        )
        
        if created:
            self.stdout.write(f'Created new port: {host.ip}:{port.port_number}/{port.proto}')
        else:
            self.stdout.write(f'Found existing port: {host.ip}:{port.port_number}/{port.proto}')
            old_time = port.last_seen
            port.last_seen = timezone.now()
            port.save()
            self.stdout.write(f'Updated port timestamp: {old_time} -> {port.last_seen}')
        
        self.stdout.write(self.style.SUCCESS('Timestamp test completed successfully!')) 