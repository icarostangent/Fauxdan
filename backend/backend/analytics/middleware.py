from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from .models import Visitor, Session, PageView
from .utils import get_client_ip, detect_device, is_bot
import json
import time

class AnalyticsMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # Skip analytics for certain paths
        if request.path.startswith('/api/analytics/') or request.path.startswith('/admin/'):
            return None
            
        # Get or create visitor
        ip_address = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        visitor, created = Visitor.objects.get_or_create(
            ip_address=ip_address,
            defaults={
                'user_agent': user_agent,
                'is_bot': is_bot(user_agent),
            }
        )
        
        if not created:
            visitor.total_visits += 1
            visitor.save()
        
        # Create or get session
        session_id = request.COOKIES.get('session_id')
        if not session_id:
            session_id = f"session_{visitor.id}_{int(time.time())}"
        
        session, _ = Session.objects.get_or_create(
            session_id=session_id,
            defaults={
                'visitor': visitor,
                'user': request.user if request.user.is_authenticated else None,
                'device_type': detect_device(user_agent)['device_type'],
                'browser': detect_device(user_agent)['browser'],
                'os': detect_device(user_agent)['os'],
            }
        )
        
        # Store in request for later use
        request.analytics_visitor = visitor
        request.analytics_session = session
        
        return None

    def process_response(self, request, response):
        if hasattr(request, 'analytics_session'):
            # Set session cookie
            response.set_cookie('session_id', request.analytics_session.session_id, max_age=3600*24)
            
            # Track page view
            if request.method == 'GET' and not request.path.startswith('/api/'):
                PageView.objects.create(
                    session=request.analytics_session,
                    url=request.build_absolute_uri(),
                    title=getattr(response, 'title', 'Unknown'),
                    referrer=request.META.get('HTTP_REFERER'),
                )
        
        return response
