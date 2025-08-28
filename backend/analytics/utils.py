import re
from django.utils import timezone
from datetime import timedelta
from .models import Session

def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def detect_device(user_agent):
    """Detect device type, browser, and OS from user agent"""
    user_agent = user_agent.lower()
    
    # Device detection
    if 'mobile' in user_agent or 'android' in user_agent or 'iphone' in user_agent:
        device_type = 'mobile'
    elif 'tablet' in user_agent or 'ipad' in user_agent:
        device_type = 'tablet'
    else:
        device_type = 'desktop'
    
    # Browser detection
    if 'chrome' in user_agent:
        browser = 'Chrome'
    elif 'firefox' in user_agent:
        browser = 'Firefox'
    elif 'safari' in user_agent:
        browser = 'Safari'
    elif 'edge' in user_agent:
        browser = 'Edge'
    else:
        browser = 'Unknown'
    
    # OS detection
    if 'windows' in user_agent:
        os = 'Windows'
    elif 'mac' in user_agent:
        os = 'macOS'
    elif 'linux' in user_agent:
        os = 'Linux'
    elif 'android' in user_agent:
        os = 'Android'
    elif 'ios' in user_agent:
        os = 'iOS'
    else:
        os = 'Unknown'
    
    return {
        'device_type': device_type,
        'browser': browser,
        'os': os
    }

def is_bot(user_agent):
    """Check if user agent is a bot"""
    bot_patterns = [
        r'bot', r'spider', r'crawler', r'scraper', r'crawling',
        r'googlebot', r'bingbot', r'slurp', r'duckduckbot',
        r'facebookexternalhit', r'twitterbot', r'linkedinbot',
        r'whatsapp', r'telegrambot', r'discordbot'
    ]
    
    user_agent_lower = user_agent.lower()
    return any(re.search(pattern, user_agent_lower) for pattern in bot_patterns)

def close_timed_out_sessions(timeout_minutes=30):
    """Close all sessions that have timed out"""
    cutoff_time = timezone.now() - timedelta(minutes=timeout_minutes)
    timed_out_sessions = Session.objects.filter(
        end_time__isnull=True,
        start_time__lt=cutoff_time
    )
    
    closed_count = 0
    for session in timed_out_sessions:
        if session.close_session():
            closed_count += 1
    
    return closed_count

def get_session_stats():
    """Get current session statistics"""
    total_sessions = Session.objects.count()
    active_sessions = Session.objects.filter(end_time__isnull=True).count()
    closed_sessions = total_sessions - active_sessions
    sessions_with_duration = Session.objects.filter(duration__isnull=False).count()
    
    return {
        'total_sessions': total_sessions,
        'active_sessions': active_sessions,
        'closed_sessions': closed_sessions,
        'sessions_with_duration': sessions_with_duration,
        'sessions_without_duration': closed_sessions - sessions_with_duration
    }
