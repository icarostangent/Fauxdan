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
from elasticsearch_dsl import Q as ElasticQ
from internet.documents import HostDocument


class ScanViewSet(viewsets.ModelViewSet):
    queryset = Scan.objects.all()
    serializer_class = ScanSerializer
    filterset_fields = []


class PortViewSet(viewsets.ModelViewSet):
    queryset = Port.objects.all()
    serializer_class = PortSerializer
    filterset_fields = ['port_number', 'proto']


class DomainViewSet(viewsets.ModelViewSet):
    queryset = Domain.objects.all()
    serializer_class = DomainSerializer
    filterset_fields = ['name',]


class HostViewSet(viewsets.ModelViewSet):
    queryset = Host.objects.all()
    serializer_class = HostSerializer
    filterset_fields = ['ip', 'domains__name']


class ProxyViewSet(viewsets.ModelViewSet):
    queryset = Proxy.objects.all()
    serializer_class = ProxySerializer
    filterset_fields = ['host_name', 'port_number', 'proxy_type', 'enabled', 'dead']


class DNSRelayViewSet(viewsets.ModelViewSet):
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


class UniversalSearchView(APIView):
    def get(self, request):
        # Get search query from request
        query = request.query_params.get('q', '')
        
        if not query:
            return Response({'error': 'No search query provided'}, status=400)
        
        # List of models to search (you can customize this)
        searchable_models = [
            {'model': Host, 'serializer': HostSerializer, 'fields': ['ip', 'domains__name', 'ports__port_number', 'ports__proto']},
        ]
        
        # Aggregate results
        results = []
        
        for model_info in searchable_models:
            # Construct Q objects for multiple search fields
            q_objects = Q()
            for field in model_info['fields']:
                q_objects |= Q(**{f'{field}__icontains': query})
            
            # Perform search and filter unique objects
            model_results = model_info['model'].objects.filter(q_objects).distinct()
            
            # Serialize results
            serializer = model_info['serializer'](model_results, many=True)
            results.extend(serializer.data)
        
        # Optional: Sort results
        # results.sort(key=lambda x: x.get('title', '').lower())
        
        return Response({
            'count': len(results),
            'results': results
        })


class ElasticSearchView(APIView):
    def get(self, request):
        query = request.query_params.get('q', '')
        page_size = int(request.query_params.get('size', 10))
        page = int(request.query_params.get('page', 1))
        
        if not query:
            return Response({'error': 'No search query provided'}, status=400)
        
        from_start = (page - 1) * page_size
        query_terms = [term.strip() for term in query.split() if term.strip()]
        
        s = HostDocument.search()
        
        must_conditions = []
        for term in query_terms:
            term_query = ElasticQ(
                'bool',
                should=[
                    # Host fields with fuzzy matching
                    ElasticQ('match', ip={'query': term, 'fuzziness': 'AUTO'}),
                    ElasticQ('match', hostname={'query': term, 'fuzziness': 'AUTO'}),
                    
                    # Domain fields (nested) with fuzzy matching
                    ElasticQ('nested', 
                        path='domains',
                        query=ElasticQ(
                            'bool',
                            should=[
                                ElasticQ('match', **{
                                    'domains.name': {
                                        'query': term,
                                        'fuzziness': 'AUTO'
                                    }
                                }),
                            ]
                        )
                    ),
                    
                    # Port fields (nested) with fuzzy matching
                    ElasticQ('nested', 
                        path='ports',
                        query=ElasticQ(
                            'bool',
                            should=[
                                ElasticQ('match', **{
                                    'ports.banner': {
                                        'query': term,
                                        'fuzziness': 'AUTO'
                                    }
                                }),
                                ElasticQ('match', **{
                                    'ports.proto': {
                                        'query': term,
                                        'fuzziness': 'AUTO'
                                    }
                                }),
                                ElasticQ('match', **{
                                    'ports.status': {
                                        'query': term,
                                        'fuzziness': 'AUTO'
                                    }
                                }),
                                ElasticQ('match', **{
                                    'ports.service': {
                                        'query': term,
                                        'fuzziness': 'AUTO'
                                    }
                                }),
                                # Port numbers should be exact matches
                                *([ElasticQ('match', **{'ports.port_number': int(term)})] 
                                  if term.isdigit() else [])
                            ]
                        )
                    )
                ],
                minimum_should_match=1
            )
            must_conditions.append(term_query)
        
        q = ElasticQ('bool', must=must_conditions)
        raw_response = s.query(q)[from_start:from_start + page_size].execute().to_dict()
        
        results = []
        for hit in raw_response['hits']['hits']:
            result = {
                'id': hit['_id'],
                'ip': hit['_source']['ip'],
                'hostname': hit['_source'].get('hostname'),
                'domains': hit['_source'].get('domains', []),
                'ports': hit['_source'].get('ports', []),
                'score': hit['_score']
            }
            results.append(result)
        
        total_count = raw_response['hits']['total']['value']
        has_next = (page * page_size) < total_count
        has_previous = page > 1
        
        return Response({
            'count': total_count,
            'next': f'?q={query}&page={page + 1}&size={page_size}' if has_next else None,
            'previous': f'?q={query}&page={page - 1}&size={page_size}' if has_previous else None,
            'page': page,
            'page_size': page_size,
            'results': results
        })