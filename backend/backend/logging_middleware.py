"""
Logging middleware to add request context to logs
"""
import logging
import time
import uuid
from threading import local

logger = logging.getLogger(__name__)
_thread_locals = local()


class RequestLoggingMiddleware:
    """Middleware to add request context to logs"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        request.request_id = request_id
        
        # Store request in thread local storage
        _thread_locals.request = request
        
        # Add request ID to logger context
        logger = logging.getLogger('django.request')
        logger = logging.LoggerAdapter(logger, {
            'request_id': request_id,
            'method': request.method,
            'path': request.path,
            'ip_address': self._get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
        })
        
        # Log request start
        start_time = time.time()
        logger.info(f"Request started: {request.method} {request.path}")
        
        # Process request
        response = self.get_response(request)
        
        # Calculate response time
        response_time = time.time() - start_time
        
        # Log request completion
        logger.info(f"Request completed: {request.method} {request.path} - {response.status_code} ({response_time:.3f}s)", 
                   extra={
                       'status_code': response.status_code,
                       'response_time': response_time,
                   })
        
        # Add request ID to response headers
        response['X-Request-ID'] = request_id
        
        # Clean up thread local storage
        if hasattr(_thread_locals, 'request'):
            delattr(_thread_locals, 'request')
            
        return response
    
    def _get_client_ip(self, request):
        """Get client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


def get_current_request():
    """Get current request from thread local storage"""
    return getattr(_thread_locals, 'request', None)
