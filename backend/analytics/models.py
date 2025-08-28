from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid
from datetime import timedelta

class Visitor(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ip_address = models.GenericIPAddressField(unique=True)
    user_agent = models.TextField(blank=True)
    is_bot = models.BooleanField(default=False)
    total_visits = models.IntegerField(default=1)
    first_visit = models.DateTimeField(default=timezone.now)
    last_visit = models.DateTimeField(default=timezone.now)
    
    class Meta:
        indexes = [
            models.Index(fields=['ip_address']),
            models.Index(fields=['is_bot']),
        ]

class Session(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    visitor = models.ForeignKey(Visitor, on_delete=models.CASCADE, related_name='sessions')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    session_id = models.CharField(max_length=100, unique=True)
    start_time = models.DateTimeField(default=timezone.now)
    end_time = models.DateTimeField(null=True, blank=True)
    duration = models.DurationField(null=True, blank=True)
    
    # Device info
    device_type = models.CharField(max_length=20, choices=[
        ('desktop', 'Desktop'),
        ('mobile', 'Mobile'),
        ('tablet', 'Tablet'),
    ])
    browser = models.CharField(max_length=50)
    os = models.CharField(max_length=50)
    
    class Meta:
        indexes = [
            models.Index(fields=['session_id']),
            models.Index(fields=['start_time']),
            models.Index(fields=['user']),
        ]
    
    def close_session(self):
        """Close the session and calculate duration"""
        if self.end_time is None:
            self.end_time = timezone.now()
            self.duration = self.end_time - self.start_time
            self.save()
            return True
        return False
    
    def is_active(self):
        """Check if session is currently active"""
        return self.end_time is None
    
    def is_timed_out(self, timeout_minutes=30):
        """Check if session has timed out based on inactivity"""
        if self.is_active():
            return timezone.now() - self.start_time > timedelta(minutes=timeout_minutes)
        return False
    
    def get_duration_display(self):
        """Get human-readable duration string"""
        if self.duration:
            total_seconds = int(self.duration.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            
            if hours > 0:
                return f"{hours}h {minutes}m {seconds}s"
            elif minutes > 0:
                return f"{minutes}m {seconds}s"
            else:
                return f"{seconds}s"
        return "Active" if self.is_active() else "Unknown"

class PageView(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='page_views')
    url = models.CharField(max_length=500, null=True, blank=True)
    title = models.CharField(max_length=200, null=True, blank=True)
    referrer = models.CharField(max_length=500, null=True, blank=True)
    timestamp = models.DateTimeField(default=timezone.now)
    time_on_page = models.DurationField(null=True, blank=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['url']),
            models.Index(fields=['timestamp']),
        ]

class Event(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='events')
    event_type = models.CharField(max_length=50)
    category = models.CharField(max_length=50)
    action = models.CharField(max_length=100)
    label = models.CharField(max_length=200, null=True, blank=True)
    value = models.IntegerField(null=True, blank=True)
    timestamp = models.DateTimeField(default=timezone.now)
    page_url = models.CharField(max_length=500, null=True, blank=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['event_type']),
            models.Index(fields=['category']),
            models.Index(fields=['timestamp']),
        ]
