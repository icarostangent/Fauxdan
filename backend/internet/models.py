import uuid
import json
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.serializers.json import DjangoJSONEncoder


class Scan(models.Model):
    scan_uuid = models.UUIDField(unique=True, default=uuid.uuid4)
    scan_command = models.TextField()
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=25, default='pending')
    scan_type = models.CharField(max_length=255, default='')
    user = models.ForeignKey(User, related_name='scans', null=True, blank=True, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.scan_uuid)


class Host(models.Model):
    ip = models.CharField(max_length=255, unique=True)
    public_host = models.ForeignKey('Host', related_name='private_hosts', on_delete=models.CASCADE, blank=True, null=True)
    private = models.BooleanField(default=False)
    scan = models.ForeignKey('Scan', related_name='hosts', null=True, blank=True, on_delete=models.CASCADE)
    last_seen = models.DateTimeField(blank=True, null=True)
    
    # Geolocation fields
    country = models.CharField(max_length=100, blank=True, null=True)
    country_code = models.CharField(max_length=2, blank=True, null=True)
    region = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    timezone = models.CharField(max_length=50, blank=True, null=True)
    isp = models.CharField(max_length=200, blank=True, null=True)
    organization = models.CharField(max_length=200, blank=True, null=True)
    asn = models.CharField(max_length=50, blank=True, null=True)
    geolocation_updated = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return str(self.ip)
    
    def update_last_seen(self):
        """Update the last_seen timestamp to current time"""
        from django.utils import timezone
        self.last_seen = timezone.now()
        self.save(update_fields=['last_seen'])
    
    def get_location_display(self):
        """Get a human-readable location string"""
        parts = []
        if self.city:
            parts.append(self.city)
        if self.region:
            parts.append(self.region)
        if self.country:
            parts.append(self.country)
        return ', '.join(parts) if parts else 'Unknown Location'
    
    def needs_geolocation_update(self, max_age_days=30):
        """Check if host needs geolocation update"""
        if not self.geolocation_updated:
            return True
        
        from django.utils import timezone
        from datetime import timedelta
        cutoff_date = timezone.now() - timedelta(days=max_age_days)
        return self.geolocation_updated < cutoff_date

    class Meta:
        indexes = [
            models.Index(fields=['ip']),  # For IP searches
            models.Index(fields=['country']),  # For location searches
            models.Index(fields=['geolocation_updated']),  # For update queries
        ]


class Port(models.Model):
    port_number = models.IntegerField()
    proto = models.CharField(max_length=3)
    status = models.CharField(max_length=25)
    last_seen = models.DateTimeField(blank=True, null=True)
    banner = models.TextField(blank=True, null=True)
    scan = models.ForeignKey('Scan', related_name='ports', on_delete=models.CASCADE)
    host = models.ForeignKey('Host', related_name='ports', on_delete=models.CASCADE)

    def __str__(self):
        return str(self.port_number)
    
    def update_last_seen(self):
        """Update the last_seen timestamp to current time"""
        from django.utils import timezone
        self.last_seen = timezone.now()
        self.save(update_fields=['last_seen'])
    
    class Meta:
        unique_together = ['host', 'port_number', 'proto']
        indexes = [
            models.Index(fields=['host']),  # For prefetch performance
            models.Index(fields=['port_number']),  # For port number searches
            models.Index(fields=['proto']),  # For protocol searches
            models.Index(fields=['banner']),  # For banner searches
        ]


class Proxy(models.Model):
    proxy_types = {'S4': 'socks4', 'S5': 'socks5', 'HP': 'HTTP', 'HS': 'HTTPS',}

    host_name = models.CharField(max_length=255)
    port_number = models.IntegerField()
    proxy_type = models.CharField(max_length=2, choices=proxy_types)
    username = models.CharField(max_length=255, blank=True, null=True)
    password = models.CharField(max_length=255, blank=True, null=True)
    enabled = models.BooleanField(default=True)
    dead = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.proxy_type}:{self.host_name}:{self.port_number}'


class Domain(models.Model):
    name = models.CharField(max_length=255)
    source = models.CharField(max_length=20, null=True, blank=True)
    host = models.ForeignKey('Host', related_name='domains', on_delete=models.CASCADE)

    def __str__(self):
        return str(self.name)
    
    class Meta:
        indexes = [
            models.Index(fields=['host']),  # For prefetch performance
            models.Index(fields=['name']),  # For domain name searches
        ]


class DNSRelay(models.Model):
    port = models.OneToOneField('Port', on_delete=models.CASCADE)

    def __str__(self):
        return str(True)


class SSLCertificate(models.Model):
    fingerprint = models.CharField(max_length=255, unique=True)
    pem_data = models.TextField()
    subject_cn = models.CharField(max_length=255, null=True, blank=True)
    issuer_cn = models.CharField(max_length=255, null=True, blank=True)
    valid_from = models.CharField(max_length=255)
    valid_until = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    port = models.ForeignKey('Port', related_name='ssl_certificates', on_delete=models.CASCADE)
    host = models.ForeignKey('Host', related_name='ssl_certificates', on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.subject_cn} ({self.fingerprint})"
    
    class Meta:
        indexes = [
            models.Index(fields=['host']),  # Critical for prefetch performance
        ]


class JobQueue(models.Model):
    """Represents a queue for scanner jobs"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    max_concurrent_jobs = models.PositiveIntegerField(default=5)
    priority = models.PositiveIntegerField(default=0, help_text="Higher number = higher priority")
    enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-priority', 'name']


class ScannerJob(models.Model):
    """Represents a scanner job in the queue"""
    
    JOB_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('queued', 'Queued'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('retrying', 'Retrying'),
    ]
    
    JOB_TYPE_CHOICES = [
        ('masscan', 'Masscan'),
        ('nmap', 'Nmap'),
        ('custom', 'Custom'),
    ]

    job_uuid = models.UUIDField(unique=True, default=uuid.uuid4)
    job_type = models.CharField(max_length=20, choices=JOB_TYPE_CHOICES, default='masscan')
    status = models.CharField(max_length=20, choices=JOB_STATUS_CHOICES, default='pending')
    priority = models.PositiveIntegerField(default=0, help_text="Higher number = higher priority")
    
    # Job configuration
    target = models.CharField(max_length=500, help_text="Target IP, range, or hostname")
    ports = models.JSONField(default=list, blank=True, help_text="List of ports to scan")
    scan_options = models.JSONField(default=dict, blank=True, help_text="Additional scan options")
    
    # Queue and worker assignment
    queue = models.ForeignKey(JobQueue, on_delete=models.CASCADE, related_name='jobs')
    assigned_worker = models.ForeignKey('JobWorker', on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_jobs')
    
    # Timing
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    scheduled_for = models.DateTimeField(null=True, blank=True, help_text="When to start the job")
    
    # Results and metadata
    scan = models.ForeignKey(Scan, on_delete=models.SET_NULL, null=True, blank=True, related_name='scanner_jobs')
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='scanner_jobs')
    retry_count = models.PositiveIntegerField(default=0)
    max_retries = models.PositiveIntegerField(default=3)
    error_message = models.TextField(blank=True)
    progress = models.PositiveIntegerField(default=0, help_text="Progress percentage (0-100)")
    
    # Job metadata
    metadata = models.JSONField(default=dict, blank=True, help_text="Additional job metadata")
    
    def __str__(self):
        return f"{self.job_type} - {self.target} ({self.status})"
    
    def can_retry(self):
        """Check if job can be retried"""
        return self.retry_count < self.max_retries and self.status in ['failed', 'cancelled']
    
    def mark_started(self):
        """Mark job as started"""
        self.status = 'running'
        self.started_at = timezone.now()
        self.save(update_fields=['status', 'started_at'])
    
    def mark_completed(self):
        """Mark job as completed"""
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.progress = 100
        self.save(update_fields=['status', 'completed_at', 'progress'])
    
    def mark_failed(self, error_message=""):
        """Mark job as failed"""
        self.status = 'failed'
        self.completed_at = timezone.now()
        self.error_message = error_message
        self.save(update_fields=['status', 'completed_at', 'error_message'])
    
    def mark_cancelled(self):
        """Mark job as cancelled"""
        self.status = 'cancelled'
        self.completed_at = timezone.now()
        self.save(update_fields=['status', 'completed_at'])
    
    def update_progress(self, progress):
        """Update job progress (0-100)"""
        self.progress = max(0, min(100, progress))
        self.save(update_fields=['progress'])
    
    class Meta:
        ordering = ['-priority', 'created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['job_type']),
            models.Index(fields=['queue', 'status']),
            models.Index(fields=['scheduled_for']),
            models.Index(fields=['assigned_worker']),
        ]


class JobWorker(models.Model):
    """Represents a worker process that can execute scanner jobs"""
    
    WORKER_STATUS_CHOICES = [
        ('active', 'Active'),
        ('idle', 'Idle'),
        ('busy', 'Busy'),
        ('offline', 'Offline'),
        ('error', 'Error'),
    ]
    
    worker_id = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=20, choices=WORKER_STATUS_CHOICES, default='idle')
    hostname = models.CharField(max_length=255)
    pid = models.PositiveIntegerField(null=True, blank=True)
    
    # Worker capabilities
    supported_job_types = models.JSONField(default=list, help_text="List of supported job types")
    max_concurrent_jobs = models.PositiveIntegerField(default=1)
    current_job_count = models.PositiveIntegerField(default=0)
    
    # Timing
    last_heartbeat = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Worker metadata
    version = models.CharField(max_length=50, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    def __str__(self):
        return f"{self.worker_id} ({self.status})"
    
    def is_available(self):
        """Check if worker can accept new jobs"""
        return (
            self.status in ['active', 'idle'] and 
            self.current_job_count < self.max_concurrent_jobs
        )
    
    def update_heartbeat(self):
        """Update worker heartbeat"""
        self.last_heartbeat = timezone.now()
        self.save(update_fields=['last_heartbeat'])
    
    def increment_job_count(self):
        """Increment current job count"""
        self.current_job_count += 1
        self.status = 'busy' if self.current_job_count > 0 else 'idle'
        self.save(update_fields=['current_job_count', 'status'])
    
    def decrement_job_count(self):
        """Decrement current job count"""
        self.current_job_count = max(0, self.current_job_count - 1)
        self.status = 'busy' if self.current_job_count > 0 else 'idle'
        self.save(update_fields=['current_job_count', 'status'])
    
    class Meta:
        ordering = ['-last_heartbeat']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['last_heartbeat']),
        ]


class AncillaryJob(models.Model):
    """Represents an ancillary job (banner grab, domain enum, SSL cert, etc.)"""
    
    JOB_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('queued', 'Queued'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('retrying', 'Retrying'),
    ]
    
    JOB_TYPE_CHOICES = [
        ('banner_grab', 'Banner Grab'),
        ('domain_enum', 'Domain Enumeration'),
        ('ssl_cert', 'SSL Certificate'),
        ('service_detection', 'Service Detection'),
        ('vulnerability_scan', 'Vulnerability Scan'),
    ]
    
    job_uuid = models.UUIDField(unique=True, default=uuid.uuid4)
    job_type = models.CharField(max_length=20, choices=JOB_TYPE_CHOICES, default='banner_grab')
    status = models.CharField(max_length=20, choices=JOB_STATUS_CHOICES, default='pending')
    priority = models.PositiveIntegerField(default=0, help_text="Higher number = higher priority")
    
    # Target information
    host_ip = models.CharField(max_length=255)
    port_number = models.PositiveIntegerField(null=True, blank=True)  # Optional for domain enum jobs
    protocol = models.CharField(max_length=3, default='tcp')
    
    # Related objects
    port = models.ForeignKey(Port, on_delete=models.CASCADE, related_name='ancillary_jobs', null=True, blank=True)
    host = models.ForeignKey(Host, on_delete=models.CASCADE, related_name='ancillary_jobs', null=True, blank=True)
    scanner_job = models.ForeignKey(ScannerJob, on_delete=models.CASCADE, related_name='ancillary_jobs', null=True, blank=True)
    
    # Worker assignment
    assigned_worker = models.ForeignKey(JobWorker, on_delete=models.SET_NULL, null=True, blank=True, related_name='ancillary_jobs')
    
    # Timing
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Results (flexible JSON field for different job types)
    result_data = models.JSONField(default=dict, blank=True, help_text="Job-specific result data")
    error_message = models.TextField(blank=True)
    retry_count = models.PositiveIntegerField(default=0)
    max_retries = models.PositiveIntegerField(default=3)
    
    # Job metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    def __str__(self):
        port_str = f":{self.port_number}" if self.port_number else ""
        return f"{self.get_job_type_display()} {self.host_ip}{port_str} ({self.status})"
    
    def can_retry(self):
        """Check if job can be retried"""
        return self.retry_count < self.max_retries and self.status in ['failed', 'cancelled']
    
    def mark_started(self):
        """Mark job as started"""
        self.status = 'running'
        self.started_at = timezone.now()
        self.save(update_fields=['status', 'started_at'])
    
    def mark_completed(self, result_data=None):
        """Mark job as completed"""
        self.status = 'completed'
        self.completed_at = timezone.now()
        if result_data:
            self.result_data = result_data
        self.save(update_fields=['status', 'completed_at', 'result_data'])
    
    def mark_failed(self, error_message=""):
        """Mark job as failed"""
        self.status = 'failed'
        self.completed_at = timezone.now()
        self.error_message = error_message
        self.save(update_fields=['status', 'completed_at', 'error_message'])
    
    def mark_cancelled(self):
        """Mark job as cancelled"""
        self.status = 'cancelled'
        self.completed_at = timezone.now()
        self.save(update_fields=['status', 'completed_at'])
    
    class Meta:
        ordering = ['-priority', 'created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['job_type']),
            models.Index(fields=['host_ip', 'port_number']),
            models.Index(fields=['assigned_worker']),
            models.Index(fields=['scanner_job']),
        ]


# Keep the old BannerGrabJob for backward compatibility
BannerGrabJob = AncillaryJob