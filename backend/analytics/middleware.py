from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from .models import Visitor, Session, PageView
from .utils import get_client_ip, detect_device, is_bot
from django.utils import timezone
from datetime import timedelta
import json
import time
import logging

logger = logging.getLogger(__name__)

class AnalyticsMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # Skip analytics for certain paths
        if (request.path.startswith('/api/analytics/') or 
            request.path.startswith('/admin/') or
            request.path.startswith('/api/health/') or
            request.path.startswith('/health/')):
            logger.debug(f"Skipping analytics for path: {request.path}")
            return None
            
        logger.debug(f"Analytics middleware processing: {request.path}")
            
        # Get client IP and user agent
        ip_address = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Skip analytics for health check tools
        if any(tool in user_agent.lower() for tool in ['curl', 'wget', 'healthcheck', 'docker']):
            logger.debug(f"Skipping analytics for tool: {user_agent}")
            return None
        
        # Skip analytics for Docker health checks (no user agent)
        if not user_agent:
            logger.debug(f"Skipping analytics for request without user agent")
            return None
        
        logger.debug(f"Processing visitor with IP: {ip_address}")
        
        visitor, created = Visitor.objects.get_or_create(
            ip_address=ip_address,
            defaults={
                'user_agent': user_agent,
                'is_bot': is_bot(user_agent),
            }
        )
        
        if created:
            logger.debug(f"Created new visitor: {visitor.id}")
        else:
            logger.debug(f"Updated existing visitor: {visitor.id}, total visits: {visitor.total_visits + 1}")
            visitor.total_visits += 1
            visitor.save()
        
        # Check for existing active session and handle timeout
        session_id = request.COOKIES.get('session_id')
        existing_session = None
        
        if session_id:
            try:
                existing_session = Session.objects.get(session_id=session_id, end_time__isnull=True)
                # Check if session has timed out (30 minutes of inactivity)
                if timezone.now() - existing_session.start_time > timedelta(minutes=30):
                    logger.debug(f"Session {existing_session.id} timed out, closing it")
                    existing_session.end_time = timezone.now()
                    existing_session.duration = existing_session.end_time - existing_session.start_time
                    existing_session.save()
                    existing_session = None
                    session_id = None  # Force new session creation
                else:
                    logger.debug(f"Using existing active session: {existing_session.id}")
            except Session.DoesNotExist:
                logger.debug(f"Session {session_id} not found, will create new one")
                session_id = None
        
        # Create new session if needed
        if not existing_session:
            if not session_id:
                session_id = f"session_{visitor.id}_{int(time.time())}"
            
            logger.debug(f"Creating new session: {session_id}")
            
            session = Session.objects.create(
                session_id=session_id,
                visitor=visitor,
                user=request.user if request.user.is_authenticated else None,
                device_type=detect_device(user_agent)['device_type'],
                browser=detect_device(user_agent)['browser'],
                os=detect_device(user_agent)['os'],
            )
            logger.debug(f"Created new session: {session.id}")
        else:
            session = existing_session
        
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
                try:
                    # Try to get title from response
                    title = 'Unknown'
                    if hasattr(response, 'context_data') and response.context_data:
                        title = response.context_data.get('title', 'Unknown')
                    elif hasattr(response, 'title'):
                        title = response.title
                    elif hasattr(response, 'context') and response.context:
                        title = response.context.get('title', 'Unknown')
                    
                    # Create page view with better title extraction
                    page_view = PageView.objects.create(
                        session=request.analytics_session,
                        url=request.build_absolute_uri(),
                        title=title,
                        referrer=request.META.get('HTTP_REFERER'),
                    )
                    logger.debug(f"Created page view: {page_view.id} for {request.path} with title: {title}")
                except Exception as e:
                    logger.error(f"Error creating page view for {request.path}: {str(e)}")
        else:
            logger.debug(f"No analytics session found for {request.path}")
        
        return response
