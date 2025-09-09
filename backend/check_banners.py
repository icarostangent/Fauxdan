#!/usr/bin/env python
import os
import sys
import django

# Add the project directory to Python path
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fauxdan.settings')
django.setup()

from internet.models import Port, AncillaryJob

print("=== BANNER GRAB STATISTICS ===")
print(f"Total ports: {Port.objects.count()}")
print(f"Ports with banners: {Port.objects.exclude(banner__isnull=True).exclude(banner='').count()}")

print("\n=== ANCILLARY JOB STATUS ===")
print(f"Banner grab jobs - Pending: {AncillaryJob.objects.filter(job_type='banner_grab', status='pending').count()}")
print(f"Banner grab jobs - Running: {AncillaryJob.objects.filter(job_type='banner_grab', status='running').count()}")
print(f"Banner grab jobs - Completed: {AncillaryJob.objects.filter(job_type='banner_grab', status='completed').count()}")
print(f"Banner grab jobs - Failed: {AncillaryJob.objects.filter(job_type='banner_grab', status='failed').count()}")

print("\n=== RECENT COMPLETED BANNER GRAB JOBS ===")
completed_jobs = AncillaryJob.objects.filter(job_type='banner_grab', status='completed').order_by('-completed_at')[:5]
for job in completed_jobs:
    banner = job.result_data.get('banner', '') if job.result_data else ''
    print(f"  {job.host_ip}:{job.port_number} - Banner: '{banner[:100]}{'...' if len(banner) > 100 else ''}'")

print("\n=== RECENT FAILED BANNER GRAB JOBS ===")
failed_jobs = AncillaryJob.objects.filter(job_type='banner_grab', status='failed').order_by('-completed_at')[:5]
for job in failed_jobs:
    error = job.error_message or 'Unknown error'
    print(f"  {job.host_ip}:{job.port_number} - Error: {error[:100]}{'...' if len(error) > 100 else ''}")

print("\n=== PORTS FOR 34.210.241.32 ===")
from internet.models import Host
host = Host.objects.filter(ip='34.210.241.32').first()
if host:
    ports = Port.objects.filter(host=host)
    print(f"Found {ports.count()} ports for 34.210.241.32:")
    for port in ports:
        banner = port.banner or 'No banner'
        print(f"  {port.port_number}/{port.proto} - Banner: '{banner}'")
else:
    print("Host 34.210.241.32 not found in database")
