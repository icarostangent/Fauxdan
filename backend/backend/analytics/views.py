from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Avg, Q
from django.utils import timezone
from datetime import timedelta
from .models import Visitor, Session, PageView, Event
from .serializers import EventSerializer

class AnalyticsViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def events(self, request):
        """Track custom events from frontend"""
        serializer = EventSerializer(data=request.data)
        if serializer.is_valid():
            event = serializer.save(session=request.analytics_session)
            return Response({'id': event.id}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Get analytics dashboard data"""
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
