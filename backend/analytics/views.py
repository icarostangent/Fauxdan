from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.db.models import Count, Avg, Q
from django.utils import timezone
from datetime import timedelta
from .models import Visitor, Session, PageView, Event
from .serializers import EventSerializer
import logging
import uuid

logger = logging.getLogger(__name__)

class AnalyticsViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]
    
    @action(detail=False, methods=['post'])
    def events(self, request):
        """Track custom events from frontend"""
        try:
            # Debug: Log the incoming data
            logger.info(f"Received analytics data: {request.data}")
            
            # Check if analytics session exists from middleware
            if hasattr(request, 'analytics_session') and request.analytics_session:
                session = request.analytics_session
                logger.info(f"Using middleware session: {session.id} (type: {type(session.id)})")
            else:
                # Create a session if middleware didn't run
                logger.warning("Analytics middleware session not found, creating fallback session")
                session = self._create_fallback_session(request)
                logger.info(f"Created fallback session: {session.id} (type: {type(session.id)})")
            
            if not session:
                logger.error("Failed to create analytics session")
                return Response(
                    {'error': 'Failed to create analytics session'}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # Add session to request data - send the UUID string, not the object
            data = request.data.copy()
            data['session'] = str(session.id)  # Convert UUID to string
            
            # Debug: Log the data being sent to serializer
            logger.info(f"Data being sent to serializer: {data}")
            logger.info(f"Session ID type: {type(data['session'])}")
            logger.info(f"Session ID value: {data['session']}")
            
            serializer = EventSerializer(data=data, context={'request': request})
            if serializer.is_valid():
                event = serializer.save()
                return Response({'id': event.id}, status=status.HTTP_201_CREATED)
            else:
                logger.error(f"Serializer errors: {serializer.errors}")
                logger.error(f"Serializer data: {serializer.initial_data}")
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Error processing analytics event: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return Response(
                {'error': 'Internal server error'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _create_fallback_session(self, request):
        """Create a fallback session when middleware isn't available"""
        try:
            # Get client IP
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip = x_forwarded_for.split(',')[0].strip()
            else:
                ip = request.META.get('REMOTE_ADDR')
            
            # Handle multiple visitors with same IP by using the most recent one
            try:
                visitor = Visitor.objects.filter(ip_address=ip).order_by('-last_visit').first()
                if visitor:
                    # Update existing visitor
                    visitor.total_visits += 1
                    visitor.last_visit = timezone.now()
                    visitor.save()
                else:
                    # Create new visitor
                    visitor = Visitor.objects.create(
                        ip_address=ip,
                        user_agent=request.META.get('HTTP_USER_AGENT', ''),
                        is_bot=False,
                    )
            except Exception as e:
                logger.error(f"Error handling visitor for IP {ip}: {str(e)}")
                # Create a new visitor with a unique identifier
                visitor = Visitor.objects.create(
                    ip_address=f"{ip}_{int(timezone.now().timestamp())}",
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    is_bot=False,
                )
            
            # Create unique session ID to prevent duplicates
            timestamp = int(timezone.now().timestamp())
            session_id = f"fallback_{visitor.id}_{timestamp}_{uuid.uuid4().hex[:8]}"
            
            session = Session.objects.create(
                visitor=visitor,
                session_id=session_id,
                device_type='desktop',  # Default value
                browser='unknown',
                os='unknown'
            )
            
            return session
            
        except Exception as e:
            logger.error(f"Error creating fallback session: {str(e)}")
            # Return None to indicate failure
            return None
    
    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def dashboard(self, request):
        """Get analytics dashboard data - keep authenticated for admin access"""
        # You might want to keep this endpoint authenticated
        from rest_framework.permissions import IsAuthenticated
        if not request.user.is_authenticated:
            return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
        
        now = timezone.now()
        last_30_days = now - timedelta(days=30)
        
        # Unique visitors
        unique_visitors = Visitor.objects.filter(
            first_visit__gte=last_30_days
        ).count()
        
        # Total page views
        total_page_views = PageView.objects.filter(
            timestamp__gte=last_30_days
        ).count()
        
        # Popular pages
        popular_pages = PageView.objects.filter(
            timestamp__gte=last_30_days
        ).values('url').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        # Device breakdown
        device_breakdown = Session.objects.filter(
            start_time__gte=last_30_days
        ).values('device_type').annotate(
            count=Count('id')
        )
        
        return Response({
            'unique_visitors': unique_visitors,
            'total_page_views': total_page_views,
            'popular_pages': popular_pages,
            'device_breakdown': device_breakdown,
        })
