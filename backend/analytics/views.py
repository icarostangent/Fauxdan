from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.db.models import Count, Avg, Q
from django.utils import timezone
from datetime import timedelta
from .models import Visitor, Session, PageView, Event
from .serializers import EventSerializer
from .utils import close_timed_out_sessions, get_session_stats
import logging
import uuid

logger = logging.getLogger(__name__)

class AnalyticsViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [AllowAny]
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    
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
            
            # Create the event
            serializer = self.get_serializer(data=data)
            if serializer.is_valid():
                event = serializer.save()
                logger.info(f"Event created successfully: {event.id}")
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                logger.error(f"Serializer errors: {serializer.errors}")
                return Response(
                    serializer.errors, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        except Exception as e:
            logger.error(f"Error processing analytics event: {str(e)}")
            return Response(
                {'error': 'Failed to process analytics event'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def session_stats(self, request):
        """Get session statistics"""
        try:
            stats = get_session_stats()
            return Response(stats, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error getting session stats: {str(e)}")
            return Response(
                {'error': 'Failed to get session statistics'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def close_sessions(self, request):
        """Close timed-out sessions"""
        try:
            timeout_minutes = request.data.get('timeout_minutes', 30)
            closed_count = close_timed_out_sessions(timeout_minutes)
            
            return Response({
                'message': f'Successfully closed {closed_count} timed-out sessions',
                'closed_count': closed_count,
                'timeout_minutes': timeout_minutes
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error closing sessions: {str(e)}")
            return Response(
                {'error': 'Failed to close sessions'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def close_session(self, request):
        """Close a specific session by ID"""
        try:
            session_id = request.data.get('session_id')
            if not session_id:
                return Response(
                    {'error': 'session_id is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            try:
                session = Session.objects.get(id=session_id)
            except Session.DoesNotExist:
                return Response(
                    {'error': 'Session not found'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            if session.close_session():
                return Response({
                    'message': 'Session closed successfully',
                    'session_id': str(session.id),
                    'duration': str(session.duration) if session.duration else None
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'message': 'Session was already closed',
                    'session_id': str(session.id)
                }, status=status.HTTP_200_OK)
                
        except Exception as e:
            logger.error(f"Error closing session: {str(e)}")
            return Response(
                {'error': 'Failed to close session'}, 
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
            return None
    
    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Get analytics dashboard data"""
        try:
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
        except Exception as e:
            logger.error(f"Error getting dashboard data: {str(e)}")
            return Response(
                {'error': 'Failed to get dashboard data'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
