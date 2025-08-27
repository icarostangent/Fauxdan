from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Count, Avg, Sum, Q
from django.utils import timezone
from datetime import timedelta
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from .models import Scan, Host, Port, Proxy, Domain, DNSRelay, SSLCertificate

# Custom admin site header and title
admin.site.site_header = "Fauxdan Internet Scanner Dashboard"
admin.site.site_title = "Fauxdan Internet Admin"
admin.site.index_title = "Welcome to Fauxdan Internet Scanner"

class ScanResource(resources.ModelResource):
    class Meta:
        model = Scan
        fields = ('id', 'scan_uuid', 'scan_command', 'start_time', 'end_time', 'status', 'scan_type', 'user')
        export_order = fields

@admin.register(Scan)
class ScanAdmin(ImportExportModelAdmin):
    resource_class = ScanResource
    list_display = ('scan_uuid', 'scan_type', 'status', 'user', 'start_time', 'end_time', 'get_duration', 'get_hosts_count')
    list_filter = ('status', 'scan_type', 'start_time', 'user')
    search_fields = ('scan_uuid', 'scan_command', 'scan_type')
    readonly_fields = ('scan_uuid', 'start_time')
    list_per_page = 50
    
    def get_duration(self, obj):
        if obj.end_time and obj.start_time:
            duration = obj.end_time - obj.start_time
            return f"{duration.total_seconds():.1f}s"
        return "Running"
    get_duration.short_description = "Duration"
    
    def get_hosts_count(self, obj):
        count = obj.hosts.count()
        return format_html('<span style="color: #007cba;">{}</span>', count)
    get_hosts_count.short_description = "Hosts Found"
    
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('hosts')

class HostResource(resources.ModelResource):
    class Meta:
        model = Host
        fields = ('id', 'ip', 'private', 'scan', 'last_seen')
        export_order = fields

@admin.register(Host)
class HostAdmin(ImportExportModelAdmin):
    resource_class = HostResource
    list_display = ('ip', 'private', 'scan', 'last_seen', 'get_ports_count', 'get_domains_count', 'get_ssl_count')
    list_filter = ('private', 'last_seen', 'scan__scan_type')
    search_fields = ('ip', 'domains__name')
    readonly_fields = ('id',)
    list_per_page = 100
    
    def get_ports_count(self, obj):
        count = obj.ports.count()
        return format_html('<span style="color: #007cba;">{}</span>', count)
    get_ports_count.short_description = "Open Ports"
    
    def get_domains_count(self, obj):
        count = obj.domains.count()
        return format_html('<span style="color: #28a745;">{}</span>', count)
    get_domains_count.short_description = "Domains"
    
    def get_ssl_count(self, obj):
        count = obj.ssl_certificates.count()
        return format_html('<span style="color: #ffc107;">{}</span>', count)
    get_ssl_count.short_description = "SSL Certs"
    
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('ports', 'domains', 'ssl_certificates')

class PortResource(resources.ModelResource):
    class Meta:
        model = Port
        fields = ('id', 'port_number', 'proto', 'status', 'last_seen', 'banner', 'scan', 'host')
        export_order = fields

@admin.register(Port)
class PortAdmin(ImportExportModelAdmin):
    resource_class = PortResource
    list_display = ('port_number', 'proto', 'status', 'host', 'scan', 'last_seen', 'get_banner_preview', 'get_ssl_info')
    list_filter = ('status', 'proto', 'port_number', 'last_seen', 'scan__scan_type')
    search_fields = ('port_number', 'host__ip', 'banner')
    readonly_fields = ('id', 'last_seen')
    list_per_page = 100
    
    def get_banner_preview(self, obj):
        if obj.banner:
            preview = obj.banner[:50] + "..." if len(obj.banner) > 50 else obj.banner
            return format_html('<span title="{}">{}</span>', obj.banner, preview)
        return "-"
    get_banner_preview.short_description = "Banner"
    
    def get_ssl_info(self, obj):
        ssl_certs = obj.ssl_certificates.all()
        if ssl_certs.exists():
            return format_html('<span style="color: #28a745;">✓ SSL</span>')
        return "-"
    get_ssl_info.short_description = "SSL"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('host', 'scan').prefetch_related('ssl_certificates')

class ProxyResource(resources.ModelResource):
    class Meta:
        model = Proxy
        fields = ('id', 'host_name', 'port_number', 'proxy_type', 'username', 'enabled', 'dead')
        export_order = fields

@admin.register(Proxy)
class ProxyAdmin(ImportExportModelAdmin):
    resource_class = ProxyResource
    list_display = ('proxy_type', 'host_name', 'port_number', 'username', 'enabled', 'dead', 'get_status')
    list_filter = ('proxy_type', 'enabled', 'dead')
    search_fields = ('host_name', 'username')
    readonly_fields = ('id',)
    list_per_page = 50
    
    def get_status(self, obj):
        if obj.dead:
            return format_html('<span style="color: #dc3545;">Dead</span>')
        elif obj.enabled:
            return format_html('<span style="color: #28a745;">Active</span>')
        else:
            return format_html('<span style="color: #6c757d;">Disabled</span>')
    get_status.short_description = "Status"

class DomainResource(resources.ModelResource):
    class Meta:
        model = Domain
        fields = ('id', 'name', 'source', 'host')
        export_order = fields

@admin.register(Domain)
class DomainAdmin(ImportExportModelAdmin):
    resource_class = DomainResource
    list_display = ('name', 'source', 'host', 'get_ip', 'get_scan_info')
    list_filter = ('source', 'host__private')
    search_fields = ('name', 'host__ip')
    readonly_fields = ('id',)
    list_per_page = 100
    
    def get_ip(self, obj):
        return obj.host.ip
    get_ip.short_description = "IP Address"
    
    def get_scan_info(self, obj):
        if obj.host.scan:
            return f"{obj.host.scan.scan_type} ({obj.host.scan.status})"
        return "-"
    get_scan_info.short_description = "Scan Info"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('host', 'host__scan')

@admin.register(DNSRelay)
class DNSRelayAdmin(admin.ModelAdmin):
    list_display = ('port', 'get_host_ip', 'get_port_number', 'get_protocol')
    list_filter = ('port__host__private',)
    search_fields = ('port__host__ip', 'port__port_number')
    
    def get_host_ip(self, obj):
        return obj.port.host.ip
    get_host_ip.short_description = "Host IP"
    
    def get_port_number(self, obj):
        return obj.port.port_number
    get_port_number.short_description = "Port"
    
    def get_protocol(self, obj):
        return obj.port.proto
    get_protocol.short_description = "Protocol"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('port__host')

class SSLCertificateResource(resources.ModelResource):
    class Meta:
        model = SSLCertificate
        fields = ('id', 'fingerprint', 'subject_cn', 'issuer_cn', 'valid_from', 'valid_until', 'port', 'host')
        export_order = fields

@admin.register(SSLCertificate)
class SSLCertificateAdmin(ImportExportModelAdmin):
    resource_class = SSLCertificateResource
    list_display = ('subject_cn', 'issuer_cn', 'host', 'port', 'valid_from', 'valid_until', 'get_fingerprint_preview')
    list_filter = ('valid_from', 'valid_until', 'port__proto')
    search_fields = ('subject_cn', 'issuer_cn', 'host__ip', 'fingerprint')
    readonly_fields = ('id', 'fingerprint', 'created_at', 'updated_at')
    list_per_page = 100
    
    def get_fingerprint_preview(self, obj):
        preview = obj.fingerprint[:16] + "..." if len(obj.fingerprint) > 16 else obj.fingerprint
        return format_html('<span title="{}">{}</span>', obj.fingerprint, preview)
    get_fingerprint_preview.short_description = "Fingerprint"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('host', 'port')

# Add internet scanner dashboard to the main admin site
class InternetScannerDashboardAdmin(admin.ModelAdmin):
    change_list_template = 'admin/internet_scanner_dashboard.html'
    
    def changelist_view(self, request, extra_context=None):
        # Get scanner data for the last 30 days
        end_date = timezone.now()
        start_date = end_date - timedelta(days=30)
        
        # Scan statistics
        total_scans = Scan.objects.count()
        active_scans = Scan.objects.filter(status='running').count()
        completed_scans = Scan.objects.filter(status='completed').count()
        failed_scans = Scan.objects.filter(status='failed').count()
        
        # Host statistics
        total_hosts = Host.objects.count()
        private_hosts = Host.objects.filter(private=True).count()
        public_hosts = Host.objects.filter(private=False).count()
        recent_hosts = Host.objects.filter(last_seen__gte=start_date).count()
        
        # Port statistics
        total_ports = Port.objects.count()
        open_ports = Port.objects.filter(status='open').count()
        closed_ports = Port.objects.filter(status='closed').count()
        
        # Service statistics by protocol
        tcp_ports = Port.objects.filter(proto='tcp').count()
        udp_ports = Port.objects.filter(proto='udp').count()
        
        # SSL certificate statistics
        total_ssl_certs = SSLCertificate.objects.count()
        recent_ssl_certs = SSLCertificate.objects.filter(created_at__gte=start_date).count()
        
        # Proxy statistics
        total_proxies = Proxy.objects.count()
        active_proxies = Proxy.objects.filter(enabled=True, dead=False).count()
        dead_proxies = Proxy.objects.filter(dead=True).count()
        
        # Domain statistics
        total_domains = Domain.objects.count()
        recent_domains = Domain.objects.filter(host__last_seen__gte=start_date).count()
        
        # Popular ports
        popular_ports = Port.objects.values('port_number').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        # Scan types distribution
        scan_types = Scan.objects.values('scan_type').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        extra_context = extra_context or {}
        extra_context.update({
            'total_scans': total_scans,
            'active_scans': active_scans,
            'completed_scans': completed_scans,
            'failed_scans': failed_scans,
            'total_hosts': total_hosts,
            'private_hosts': private_hosts,
            'public_hosts': public_hosts,
            'recent_hosts': recent_hosts,
            'total_ports': total_ports,
            'open_ports': open_ports,
            'closed_ports': closed_ports,
            'tcp_ports': tcp_ports,
            'udp_ports': udp_ports,
            'total_ssl_certs': total_ssl_certs,
            'recent_ssl_certs': recent_ssl_certs,
            'total_proxies': total_proxies,
            'active_proxies': active_proxies,
            'dead_proxies': dead_proxies,
            'total_domains': total_domains,
            'recent_domains': recent_domains,
            'popular_ports': popular_ports,
            'scan_types': scan_types,
            'start_date': start_date,
            'end_date': end_date,
        })
        
        return super().changelist_view(request, extra_context)

# Register the dashboard as a separate model (we'll use a proxy model)
from django.contrib.admin.models import LogEntry

class InternetScannerDashboard(LogEntry):
    class Meta:
        proxy = True
        verbose_name = "Internet Scanner Dashboard"
        verbose_name_plural = "Internet Scanner Dashboard"

admin.site.register(InternetScannerDashboard, InternetScannerDashboardAdmin)
