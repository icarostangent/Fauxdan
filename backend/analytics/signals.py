from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Session, PageView
import logging

logger = logging.getLogger(__name__)

@receiver(pre_save, sender=Session)
def calculate_session_duration(sender, instance, **kwargs):
    """Automatically calculate session duration when session is closed"""
    if instance.end_time and not instance.duration:
        instance.duration = instance.end_time - instance.start_time
        logger.debug(f"Calculated duration for session {instance.id}: {instance.duration}")

@receiver(post_save, sender=PageView)
def update_session_activity(sender, instance, created, **kwargs):
    """Update session activity when new page view is created"""
    if created and instance.session:
        # This could be used to extend session timeout or track last activity
        logger.debug(f"New page view for session {instance.session.id}: {instance.url}")

@receiver(post_save, sender=Session)
def log_session_changes(sender, instance, created, **kwargs):
    """Log session creation and closure for debugging"""
    if created:
        logger.info(f"New session created: {instance.id} for visitor {instance.visitor.ip_address}")
    elif instance.end_time:
        logger.info(f"Session closed: {instance.id}, duration: {instance.duration}")
