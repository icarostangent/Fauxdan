from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import models
from internet.models import Host, AncillaryJob
from internet.lib.geolocation import get_ip_geolocation_async, get_ip_geolocations_batch_async
import asyncio
import time
from datetime import timedelta


class Command(BaseCommand):
    help = 'Geolocate hosts in the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Number of hosts to process in each batch'
        )
        parser.add_argument(
            '--delay',
            type=float,
            default=0.1,
            help='Delay between requests in seconds (for rate limiting)'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force re-geolocate all hosts, even if already geolocated'
        )
        parser.add_argument(
            '--max-age-days',
            type=int,
            default=30,
            help='Re-geolocate hosts older than this many days'
        )
        parser.add_argument(
            '--ip',
            type=str,
            help='Geolocate a specific IP address'
        )
        parser.add_argument(
            '--queue-jobs',
            action='store_true',
            help='Queue geolocation jobs instead of processing directly'
        )
        parser.add_argument(
            '--async-batch',
            action='store_true',
            help='Use async batch processing for direct geolocation'
        )

    def handle(self, *args, **options):
        batch_size = options['batch_size']
        delay = options['delay']
        force = options['force']
        max_age_days = options['max_age_days']
        specific_ip = options['ip']
        queue_jobs = options['queue_jobs']
        async_batch = options['async_batch']

        if specific_ip:
            if async_batch:
                asyncio.run(self.geolocate_single_ip_async(specific_ip))
            else:
                self.geolocate_single_ip(specific_ip)
            return

        # Determine which hosts need geolocation
        if force:
            hosts = Host.objects.all()
            self.stdout.write(f"Force mode: Processing all {hosts.count()} hosts")
        else:
            # Get hosts that haven't been geolocated or are old
            cutoff_date = timezone.now() - timedelta(days=max_age_days)
            hosts = Host.objects.filter(
                models.Q(geolocation_updated__isnull=True) |
                models.Q(geolocation_updated__lt=cutoff_date)
            )
            self.stdout.write(f"Processing {hosts.count()} hosts that need geolocation updates")

        if hosts.count() == 0:
            self.stdout.write(self.style.SUCCESS("No hosts need geolocation updates"))
            return

        if queue_jobs:
            # Queue geolocation jobs
            self.queue_geolocation_jobs(hosts)
        elif async_batch:
            # Use async batch processing
            asyncio.run(self.process_hosts_async_batch(hosts, batch_size))
        else:
            # Use original sequential processing
            self.process_hosts_sequential(hosts, batch_size, delay)

    def geolocate_single_ip(self, ip_address):
        """Geolocate a single IP address for testing"""
        self.stdout.write(f"Geolocating {ip_address}...")
        
        location_data = get_ip_geolocation(ip_address)
        
        if location_data:
            self.stdout.write(self.style.SUCCESS("Geolocation successful:"))
            for key, value in location_data.items():
                self.stdout.write(f"  {key}: {value}")
        else:
            self.stdout.write(self.style.ERROR("Geolocation failed"))

    def geolocate_host(self, host):
        """Geolocate a single host and update the database"""
        try:
            # Skip private IP addresses
            if self.is_private_ip(host.ip):
                self.stdout.write(f"Skipping private IP: {host.ip}")
                return False

            location_data = get_ip_geolocation(host.ip)
            
            if location_data:
                # Update host with geolocation data
                host.country = location_data.get('country')
                host.country_code = location_data.get('country_code')
                host.region = location_data.get('region')
                host.city = location_data.get('city')
                host.latitude = location_data.get('latitude')
                host.longitude = location_data.get('longitude')
                host.timezone = location_data.get('timezone')
                host.isp = location_data.get('isp')
                host.organization = location_data.get('organization')
                host.asn = location_data.get('asn')
                host.geolocation_updated = timezone.now()
                host.save()
                
                self.stdout.write(
                    f"✓ {host.ip} -> {location_data.get('city', 'Unknown')}, "
                    f"{location_data.get('country', 'Unknown')} "
                    f"({location_data.get('provider', 'Unknown')})"
                )
                return True
            else:
                self.stdout.write(f"✗ Failed to geolocate {host.ip}")
                # Still update the timestamp to avoid repeated attempts
                host.geolocation_updated = timezone.now()
                host.save()
                return False
                
        except Exception as e:
            self.stdout.write(f"✗ Error geolocating {host.ip}: {e}")
            return False

    def is_private_ip(self, ip):
        """Check if IP address is private/internal"""
        import ipaddress
        try:
            ip_obj = ipaddress.ip_address(ip)
            return ip_obj.is_private
        except ValueError:
            return False

    def queue_geolocation_jobs(self, hosts):
        """Queue geolocation jobs for hosts"""
        total_queued = 0
        total_skipped = 0
        
        for host in hosts:
            try:
                # Check if job already exists
                existing_job = AncillaryJob.objects.filter(
                    host=host,
                    job_type='geolocation',
                    status__in=['pending', 'running', 'queued']
                ).exists()
                
                if existing_job:
                    total_skipped += 1
                    continue
                
                # Skip private IPs
                if self.is_private_ip(host.ip):
                    total_skipped += 1
                    continue
                
                # Create geolocation job
                AncillaryJob.objects.create(
                    job_type='geolocation',
                    host_ip=host.ip,
                    host=host,
                    status='pending',
                    priority=2
                )
                total_queued += 1
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Error queuing job for {host.ip}: {e}")
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f"Job queuing complete! Queued: {total_queued}, Skipped: {total_skipped}"
            )
        )

    async def geolocate_single_ip_async(self, ip_address):
        """Async version of single IP geolocation"""
        self.stdout.write(f"Geolocating {ip_address} (async)...")
        
        location_data = await get_ip_geolocation_async(ip_address)
        
        if location_data:
            self.stdout.write(self.style.SUCCESS("Geolocation successful:"))
            for key, value in location_data.items():
                self.stdout.write(f"  {key}: {value}")
        else:
            self.stdout.write(self.style.ERROR("Geolocation failed"))

    async def process_hosts_async_batch(self, hosts, batch_size):
        """Process hosts using async batch geolocation"""
        from asgiref.sync import sync_to_async
        
        total_processed = 0
        total_success = 0
        total_failed = 0
        
        # Convert queryset to list and filter out private IPs (sync context)
        def get_host_list():
            host_list = []
            for host in hosts:
                if not self.is_private_ip(host.ip):
                    host_list.append(host)
            return host_list
        
        host_list = await sync_to_async(get_host_list)()
        
        self.stdout.write(f"Processing {len(host_list)} public hosts with async batch processing...")
        
        # Process in batches
        for i in range(0, len(host_list), batch_size):
            batch = host_list[i:i + batch_size]
            batch_ips = [host.ip for host in batch]
            
            self.stdout.write(f"Processing async batch {i//batch_size + 1} ({len(batch)} hosts)...")
            
            # Get geolocation data for entire batch
            results = await get_ip_geolocations_batch_async(batch_ips, batch_size)
            
            # Update hosts with results
            for host in batch:
                try:
                    location_data = results.get(host.ip)
                    
                    def update_host_data():
                        if location_data:
                            # Update host with geolocation data
                            host.country = location_data.get('country')
                            host.country_code = location_data.get('country_code')
                            host.region = location_data.get('region')
                            host.city = location_data.get('city')
                            host.latitude = location_data.get('latitude')
                            host.longitude = location_data.get('longitude')
                            host.timezone = location_data.get('timezone')
                            host.isp = location_data.get('isp')
                            host.organization = location_data.get('organization')
                            host.asn = location_data.get('asn')
                            host.geolocation_updated = timezone.now()
                            host.save()
                            return True
                        else:
                            # Still update the timestamp to avoid repeated attempts
                            host.geolocation_updated = timezone.now()
                            host.save(update_fields=['geolocation_updated'])
                            return False
                    
                    success = await sync_to_async(update_host_data)()
                    
                    if success:
                        self.stdout.write(
                            f"✓ {host.ip} -> {location_data.get('city', 'Unknown')}, "
                            f"{location_data.get('country', 'Unknown')} "
                            f"({location_data.get('provider', 'Unknown')})"
                        )
                        total_success += 1
                    else:
                        self.stdout.write(f"✗ Failed to geolocate {host.ip}")
                        total_failed += 1
                    
                    total_processed += 1
                    
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"Error updating {host.ip}: {e}")
                    )
                    total_failed += 1
                    total_processed += 1
            
            # Progress update
            self.stdout.write(
                f"Async batch complete. Progress: {total_processed}/{len(host_list)} "
                f"(Success: {total_success}, Failed: {total_failed})"
            )
        
        self.stdout.write(
            self.style.SUCCESS(
                f"Async batch processing complete! "
                f"Processed: {total_processed}, "
                f"Success: {total_success}, "
                f"Failed: {total_failed}"
            )
        )

    def process_hosts_sequential(self, hosts, batch_size, delay):
        """Original sequential processing method"""
        total_processed = 0
        total_success = 0
        total_failed = 0

        for i in range(0, hosts.count(), batch_size):
            batch = hosts[i:i + batch_size]
            self.stdout.write(f"Processing batch {i//batch_size + 1} ({len(batch)} hosts)...")

            for host in batch:
                try:
                    success = self.geolocate_host(host)
                    if success:
                        total_success += 1
                    else:
                        total_failed += 1
                    
                    total_processed += 1
                    
                    # Rate limiting
                    if delay > 0:
                        time.sleep(delay)
                        
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"Error processing {host.ip}: {e}")
                    )
                    total_failed += 1
                    total_processed += 1

            # Progress update
            self.stdout.write(
                f"Batch complete. Progress: {total_processed}/{hosts.count()} "
                f"(Success: {total_success}, Failed: {total_failed})"
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Sequential processing complete! "
                f"Processed: {total_processed}, "
                f"Success: {total_success}, "
                f"Failed: {total_failed}"
            )
        )
