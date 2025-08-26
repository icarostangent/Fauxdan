from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Count, Avg, Sum, Q
from django.utils import timezone
from datetime import timedelta
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from .models import Visitor, Session, PageView, Event

# Custom admin site header and title
admin.site.site_header = "Fauxdan Analytics Dashboard"
admin.site.site_title = "Fauxdan Admin"
admin.site.index_title = "Welcome to Fauxdan Analytics"

class VisitorResource(resources.ModelResource):
    class Meta:
        model = Visitor
        fields = ('id', 'ip_address', 'user_agent', 'first_visit', 'last_visit', 'total_visits', 'is_bot', 'country', 'city', 'timezone')
        export_order = fields

@admin.register(Visitor)
class VisitorAdmin(ImportExportModelAdmin):
    resource_class = VisitorResource
    list_display = ('ip_address', 'country', 'city', 'total_visits', 'first_visit', 'last_visit', 'is_bot', 'get_device_info')
    list_filter = ('is_bot', 'country', 'city', 'timezone', 'first_visit')
    search_fields = ('ip_address', 'country', 'city', 'user_agent')
    readonly_fields = ('id', 'first_visit', 'last_visit', 'total_visits')
    list_per_page = 50
    
    def get_device_info(self, obj):
        # Get device info from related sessions
        sessions = obj.sessions.all()
        if sessions.exists():
            device_types = set(s.device_type for s in sessions)
            browsers = set(s.browser for s in sessions)
            # Convert set to list before slicing
            browser_list = list(browsers)
            return f"{', '.join(device_types)} | {', '.join(browser_list[:2])}"
        return "No sessions"
    get_device_info.short_description = "Device Info"
    
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('sessions')

class SessionResource(resources.ModelResource):
    class Meta:
        model = Session
        fields = ('id', 'visitor', 'user', 'session_id', 'start_time', 'end_time', 'duration', 'device_type', 'browser', 'os')
        export_order = fields

@admin.register(Session)
class SessionAdmin(ImportExportModelAdmin):
    resource_class = SessionResource
    list_display = ('session_id', 'visitor', 'user', 'device_type', 'browser', 'os', 'start_time', 'duration', 'get_page_views_count')
    list_filter = ('device_type', 'browser', 'os', 'start_time')
    search_fields = ('session_id', 'visitor__ip_address', 'user__username')
    readonly_fields = ('id', 'start_time')
    list_per_page = 50
    
    def get_page_views_count(self, obj):
        count = obj.page_views.count()
        return format_html('<span style="color: #007cba;">{}</span>', count)
    get_page_views_count.short_description = "Page Views"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('visitor', 'user').prefetch_related('page_views')

class PageViewResource(resources.ModelResource):
    class Meta:
        model = PageView
        fields = ('id', 'session', 'url', 'title', 'referrer', 'timestamp', 'time_on_page')
        export_order = fields

@admin.register(PageView)
class PageViewAdmin(ImportExportModelAdmin):
    resource_class = PageViewResource
    list_display = ('url', 'title', 'session', 'timestamp', 'time_on_page', 'referrer')
    list_filter = ('timestamp', 'session__device_type')
    search_fields = ('url', 'title', 'session__session_id')
    readonly_fields = ('id', 'timestamp')
    list_per_page = 100
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('session', 'session__visitor')

class EventResource(resources.ModelResource):
    class Meta:
        model = Event
        fields = ('id', 'session', 'event_type', 'category', 'action', 'label', 'value', 'timestamp', 'page_url')
        export_order = fields

@admin.register(Event)
class EventAdmin(ImportExportModelAdmin):
    resource_class = EventResource
    list_display = ('event_type', 'category', 'action', 'label', 'value', 'session', 'timestamp')
    list_filter = ('event_type', 'category', 'timestamp')
    search_fields = ('event_type', 'category', 'action', 'label')
    readonly_fields = ('id', 'timestamp')
    list_per_page = 100
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('session', 'session__visitor')

# Add analytics dashboard to the main admin site
class AnalyticsDashboardAdmin(admin.ModelAdmin):
    change_list_template = 'admin/analytics_dashboard.html'
    
    def changelist_view(self, request, extra_context=None):
        # Get analytics data for the last 30 days
        end_date = timezone.now()
        start_date = end_date - timedelta(days=30)
        
        # Visitor statistics
        total_visitors = Visitor.objects.count()
        new_visitors = Visitor.objects.filter(first_visit__gte=start_date).count()
        returning_visitors = Visitor.objects.filter(last_visit__gte=start_date, total_visits__gt=1).count()
        
        # Session statistics
        total_sessions = Session.objects.count()
        active_sessions = Session.objects.filter(end_time__isnull=True).count()
        avg_session_duration = Session.objects.filter(duration__isnull=False).aggregate(avg=Avg('duration'))
        
        # Page view statistics
        total_page_views = PageView.objects.count()
        popular_pages = PageView.objects.values('url', 'title').annotate(
            view_count=Count('id')
        ).order_by('-view_count')[:10]
        
        # Device statistics
        device_stats = Session.objects.values('device_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Browser statistics
        browser_stats = Session.objects.values('browser').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        # Geographic statistics
        country_stats = Visitor.objects.values('country').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        extra_context = extra_context or {}
        extra_context.update({
            'total_visitors': total_visitors,
            'new_visitors': new_visitors,
            'returning_visitors': returning_visitors,
            'total_sessions': total_sessions,
            'active_sessions': active_sessions,
            'avg_session_duration': avg_session_duration.get('avg'),
            'total_page_views': total_page_views,
            'popular_pages': popular_pages,
            'device_stats': device_stats,
            'browser_stats': browser_stats,
            'country_stats': country_stats,
            'start_date': start_date,
            'end_date': end_date,
        })
        
        return super().changelist_view(request, extra_context)

# Register the dashboard as a separate model (we'll use a proxy model)
from django.contrib.admin.models import LogEntry

class AnalyticsDashboard(LogEntry):
    class Meta:
        proxy = True
        verbose_name = "Analytics Dashboard"
        verbose_name_plural = "Analytics Dashboard"

admin.site.register(AnalyticsDashboard, AnalyticsDashboardAdmin)
