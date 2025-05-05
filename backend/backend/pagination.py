from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from urllib.parse import urlparse
from django.conf import settings

class PathOnlyPagination(PageNumberPagination):
    def get_paginated_response(self, data):
        next_url = self.get_next_link()
        previous_url = self.get_previous_link()

        # Extract path and query parameters, excluding domain
        if next_url:
            parsed = urlparse(next_url)
            next_path = f"{parsed.path}?{parsed.query}"  # Combines /api/hosts/ with ?page=2
        else:
            next_path = None

        if previous_url:
            parsed = urlparse(previous_url)
            previous_path = f"{parsed.path}?{parsed.query}"
        else:
            previous_path = None

        return Response({
            'count': self.page.paginator.count,
            'next': next_path,
            'page': self.page.number,
            'page_size': settings.REST_FRAMEWORK['PAGE_SIZE'],
            'previous': previous_path,
            'results': data,
        })
