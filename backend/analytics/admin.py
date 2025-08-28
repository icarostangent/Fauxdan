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
        fields = ('id', 'ip_address', 'user_agent', 'is_bot', 'total_visits', 'first_visit', 'last_visit')
        export_order = fields

@admin.register(Visitor)
class VisitorAdmin(ImportExportModelAdmin):
    resource_class = VisitorResource
    list_display = ('ip_address', 'is_bot', 'total_visits', 'first_visit', 'last_visit', 'get_sessions_count')
    list_filter = ('is_bot', 'first_visit', 'last_visit')
    search_fields = ('ip_address', 'user_agent')
    readonly_fields = ('id', 'first_visit')
    list_per_page = 50
    
    def get_sessions_count(self, obj):
        count = obj.sessions.count()
        return format_html('<span style="color: #007cba;">{}</span>', count)
    get_sessions_count.short_description = "Sessions"
    
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
    list_display = ('session_id', 'visitor', 'user', 'device_type', 'browser', 'os', 'start_time', 'get_duration_display', 'get_status', 'get_page_views_count')
    list_filter = ('device_type', 'browser', 'os', 'start_time', 'end_time')
    search_fields = ('session_id', 'visitor__ip_address', 'user__username')
    readonly_fields = ('id', 'start_time', 'get_duration_display', 'get_status')
    list_per_page = 50
    actions = ['close_selected_sessions', 'calculate_durations']
    
    def get_duration_display(self, obj):
        return obj.get_duration_display()
    get_duration_display.short_description = "Duration"
    
    def get_status(self, obj):
        if obj.is_active():
            return format_html('<span style="color: #28a745;">Active</span>')
        else:
            return format_html('<span style="color: #6c757d;">Closed</span>')
    get_status.short_description = "Status"
    
    def get_page_views_count(self, obj):
        count = obj.page_views.count()
        return format_html('<span style="color: #007cba;">{}</span>', count)
    get_page_views_count.short_description = "Page Views"
    
    def close_selected_sessions(self, request, queryset):
        """Admin action to close selected sessions"""
        active_sessions = queryset.filter(end_time__isnull=True)
        closed_count = 0
        
        for session in active_sessions:
            if session.close_session():
                closed_count += 1
        
        self.message_user(
            request,
            f'Successfully closed {closed_count} out of {queryset.count()} selected sessions.'
        )
    close_selected_sessions.short_description = "Close selected sessions"
    
    def calculate_durations(self, request, queryset):
        """Admin action to calculate durations for closed sessions"""
        sessions_without_duration = queryset.filter(
            end_time__isnot=None,
            duration__isnull=True
        )
        calculated_count = 0
        
        for session in sessions_without_duration:
            session.duration = session.end_time - session.start_time
            session.save()
            calculated_count += 1
        
        self.message_user(
            request,
            f'Successfully calculated durations for {calculated_count} out of {queryset.count()} selected sessions.'
        )
    calculate_durations.short_description = "Calculate durations for closed sessions"
    
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
        
        # Geographic statistics (removed country stats as field doesn't exist)
        
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
