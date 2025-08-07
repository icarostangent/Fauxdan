import uuid
from django.db import models
from django.contrib.auth.models import User


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

    def __str__(self):
        return str(self.ip)
    
    def update_last_seen(self):
        """Update the last_seen timestamp to current time"""
        from django.utils import timezone
        self.last_seen = timezone.now()
        self.save(update_fields=['last_seen'])


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