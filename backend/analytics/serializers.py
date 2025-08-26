from rest_framework import serializers
from .models import Event
import logging

logger = logging.getLogger(__name__)

class EventSerializer(serializers.ModelSerializer):
    # Add these fields to accept frontend data
    event = serializers.CharField(write_only=True, required=False)
    page = serializers.CharField(write_only=True, required=False)
    
    class Meta:
        model = Event
        fields = [
            'id', 'event_type', 'category', 'action', 'label', 
            'value', 'timestamp', 'session', 'page_url', 'event', 'page'
        ]
        read_only_fields = ['id', 'timestamp']
    
    def validate_session(self, value):
        """Validate session field"""
        logger.info(f"Validating session field: {value} (type: {type(value)})")
        return value
    
    def create(self, validated_data):
        # Map frontend fields to model fields
        if 'event' in validated_data:
            validated_data['event_type'] = validated_data.pop('event')
        
        if 'page' in validated_data:
            validated_data['page_url'] = validated_data.pop('page')
        
        # Create the event
        return Event.objects.create(**validated_data)
