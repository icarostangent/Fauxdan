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

class UserStory(Session):
    """Proxy model for displaying user stories in admin"""
    
    class Meta:
        verbose_name = "User Story"
        verbose_name_plural = "User Stories"
        proxy = True
    
    def get_visitor_info(self):
        """Get visitor information for display"""
        return {
            'ip_address': self.visitor.ip_address,
            'user_agent': self.visitor.user_agent,
            'is_bot': self.visitor.is_bot,
            'total_visits': self.visitor.total_visits,
        }
    
    def get_session_info(self):
        """Get session information for display"""
        return {
            'session_id': self.session_id,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'duration': self.get_duration_display(),
            'device_type': self.device_type,
            'browser': self.browser,
            'os': self.os,
            'status': 'Active' if self.is_active() else 'Closed',
        }
    
    def get_page_views(self):
        """Get all page views for this session"""
        return self.page_views.all().order_by('timestamp')
    
    def get_events(self):
        """Get all events for this session"""
        return self.events.all().order_by('timestamp')
    
    def get_user_journey(self):
        """Get the complete user journey as a timeline"""
        journey = []
        
        # Add session start
        journey.append({
            'type': 'session_start',
            'timestamp': self.start_time,
            'description': f'Session started on {self.device_type} using {self.browser}',
            'icon': '🚀'
        })
        
        # Add page views
        for page_view in self.get_page_views():
            journey.append({
                'type': 'page_view',
                'timestamp': page_view.timestamp,
                'description': f'Viewed: {page_view.title or page_view.url}',
                'url': page_view.url,
                'icon': '📄'
            })
        
        # Add events
        for event in self.get_events():
            journey.append({
                'type': 'event',
                'timestamp': event.timestamp,
                'description': f'{event.category}: {event.action}',
                'label': event.label,
                'value': event.value,
                'icon': '🎯'
            })
        
        # Add session end if closed
        if self.end_time:
            journey.append({
                'type': 'session_end',
                'timestamp': self.end_time,
                'description': f'Session ended - Duration: {self.get_duration_display()}',
                'icon': '🏁'
            })
        
        # Sort by timestamp
        journey.sort(key=lambda x: x['timestamp'])
        return journey
