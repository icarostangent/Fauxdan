from django.db.models import Q
from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from internet.models import Scan, Host, Domain, Port, Proxy, DNSRelay
from internet.serializers import (
    ScanSerializer, HostSerializer, DomainSerializer, PortSerializer, 
    ProxySerializer, DNSRelaySerializer
)
from django.core.management import call_command
from rest_framework import status
from rest_framework.generics import ListAPIView
from backend.pagination import PathOnlyPagination


class ScanViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Scan.objects.all()
    serializer_class = ScanSerializer
    filterset_fields = []


class PortViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Port.objects.all()
    serializer_class = PortSerializer
    filterset_fields = ['port_number', 'proto']


class DomainViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Domain.objects.all()
    serializer_class = DomainSerializer
    filterset_fields = ['name',]


class HostViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Host.objects.prefetch_related(
        'ports',
        'domains', 
        'ssl_certificates'
    ).select_related('scan')
    serializer_class = HostSerializer
    filterset_fields = ['ip', 'domains__name']
    
    def list(self, request, *args, **kwargs):
        try:
            response = super().list(request, *args, **kwargs)
            return response
        except Exception as e:
            raise


class ProxyViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Proxy.objects.all()
    serializer_class = ProxySerializer
    filterset_fields = ['host_name', 'port_number', 'proxy_type', 'enabled', 'dead']


class DNSRelayViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = DNSRelay.objects.all()
    serializer_class = DNSRelaySerializer
    # filterset_fields = ['port',]


class CreateScanView(APIView):
    SCAN_TYPES = {
        'port_scan': 'port_scan',
        'enumerate_domains': 'enumerate_domains',
    }

    def post(self, request):
        # Validate required fields
        scan_type = request.data.get('scan_type')
        user_id = request.data.get('user_id')
        host_id = request.data.get('host_id')

        # Check all required fields are present
        if not all([scan_type, user_id, host_id]):
            return Response(
                {'error': 'scan_type, user_id, and host_id are all required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate scan type
        if scan_type not in self.SCAN_TYPES:
            return Response(
                {'error': f'Invalid scan_type. Must be one of: {", ".join(self.SCAN_TYPES.keys())}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Verify host exists
            try:
                host = Host.objects.get(id=host_id)
            except Host.DoesNotExist:
                return Response(
                    {'error': f'Host with ID {host_id} not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

        except Exception as e:
            return Response(
                {'error': f'Failed to create scan: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        # Create scan record
        scan = Scan.objects.create(
            scan_type=scan_type,
            user_id=user_id,
            status='pending'
           )

        # Handle different scan types
        if scan_type == 'port_scan':
            call_command('run_masscan', f'--target={host.ip}')
            # chain(
                #     periodic_collector_task.s()
                # ).apply_async()

        elif scan_type == 'enumerate_domains':
            call_command('schedule_enumerate_domains', f'--target={host.id}')
            # chain(
                #     process_ssl_queue_task.s()
                # ).apply_async()

        # Update scan status
        scan.status = 'running'
        scan.save()

        return Response({
            'message': 'Scan created successfully',
            'scan_id': scan.id,
            'host_id': host.id,
            'host_ip': host.ip,
            'status': scan.status
        }, status=status.HTTP_201_CREATED)


class UniversalSearchView(ListAPIView):
    serializer_class = HostSerializer
    pagination_class = PathOnlyPagination
    
    def get_queryset(self):
        query = self.request.query_params.get('q', '')
        if not query:
            return Host.objects.none()
        
        # More intelligent search logic
        q_objects = Q()
        
        # IP address search (exact or partial)
        if self._is_valid_ip(query):
            q_objects |= Q(ip__icontains=query)
        
        # Domain search (only if it looks like a domain)
        if '.' in query and not query.isdigit():
            q_objects |= Q(domains__name__icontains=query)
        
        # Port search (only if it's a valid port number)
        if query.isdigit() and 1 <= int(query) <= 65535:
            # Use exact match instead of icontains for ports
            q_objects |= Q(ports__port_number=int(query))
        
        # Protocol search (only if it's a valid protocol)
        if query.lower() in ['tcp', 'udp']:
            q_objects |= Q(ports__proto__iexact=query)
        
        # Add prefetch_related to prevent N+1 queries
        return Host.objects.filter(q_objects).prefetch_related(
            'ports',
            'domains', 
            'ssl_certificates'
        ).select_related('scan').distinct()
    
    def _is_valid_ip(self, query):
        """Check if query looks like a valid IP address"""
        import re
        ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        if re.match(ip_pattern, query):
            parts = query.split('.')
            return all(0 <= int(part) <= 255 for part in parts)
        return False