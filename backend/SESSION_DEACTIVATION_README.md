# Session Deactivation Implementation

This document describes the session deactivation functionality implemented in the analytics system.

## Overview

The session deactivation system automatically manages user sessions by:
- Closing sessions after a configurable timeout period
- Calculating session durations
- Providing admin tools for session management
- Offering API endpoints for session control

## Features

### 1. Automatic Session Timeout
- Sessions automatically close after 30 minutes of inactivity
- Timeout is configurable via middleware settings
- Sessions are marked with `end_time` and `duration` when closed

### 2. Session Management Methods
- `close_session()`: Manually close a session
- `is_active()`: Check if session is currently active
- `is_timed_out()`: Check if session has timed out
- `get_duration_display()`: Get human-readable duration string

### 3. Admin Interface Enhancements
- Session status display (Active/Closed)
- Duration information with human-readable format
- Admin actions for bulk session closure
- Duration calculation for existing sessions

### 4. API Endpoints
- `GET /api/analytics/session_stats/`: Get session statistics
- `POST /api/analytics/close_sessions/`: Close timed-out sessions
- `POST /api/analytics/close_session/`: Close specific session

### 5. Management Commands
- `cleanup_sessions`: Clean up old sessions and calculate durations
- Configurable timeout periods
- Dry-run mode for testing

## Usage

### Running the Cleanup Command

```bash
# Show what would be cleaned up (dry run)
python manage.py cleanup_sessions --dry-run

# Clean up sessions older than 24 hours (default)
python manage.py cleanup_sessions

# Clean up sessions older than 12 hours
python manage.py cleanup_sessions --timeout-hours 12

# Force close all active sessions
python manage.py cleanup_sessions --force-all
```

### Using the API

```bash
# Get session statistics
curl -X GET http://localhost:8000/api/analytics/session_stats/

# Close timed-out sessions
curl -X POST http://localhost:8000/api/analytics/close_sessions/ \
  -H "Content-Type: application/json" \
  -d '{"timeout_minutes": 30}'

# Close specific session
curl -X POST http://localhost:8000/api/analytics/close_session/ \
  -H "Content-Type: application/json" \
  -d '{"session_id": "uuid-here"}'
```

### Admin Interface

1. Navigate to Django Admin → Analytics → Sessions
2. View session status and duration information
3. Use bulk actions to close multiple sessions
4. Calculate durations for existing sessions

## Configuration

### Middleware Settings

The session timeout is configured in the `AnalyticsMiddleware`:

```python
# backend/analytics/middleware.py
# Check if session has timed out (30 minutes of inactivity)
if timezone.now() - existing_session.start_time > timedelta(minutes=30):
    # Close session and create new one
```

### Signal Handlers

Automatic duration calculation is handled by Django signals:

```python
# backend/analytics/signals.py
@receiver(pre_save, sender=Session)
def calculate_session_duration(sender, instance, **kwargs):
    if instance.end_time and not instance.duration:
        instance.duration = instance.end_time - instance.start_time
```

## Testing

### Run the Test Script

```bash
cd backend
python test_session_deactivation.py
```

This script will:
1. Create test sessions (active, timed-out, closed)
2. Test timeout detection
3. Test session closure
4. Test utility functions
5. Clean up test data

### Manual Testing

1. Create a session in the admin interface
2. Wait for timeout or manually close it
3. Verify duration is calculated
4. Check session status changes

## Database Schema

### Session Model Fields

- `start_time`: When session started (auto-set)
- `end_time`: When session ended (null for active sessions)
- `duration`: Calculated duration (null for active sessions)

### Indexes

- `session_id`: For fast session lookup
- `start_time`: For timeout queries
- `end_time`: For active session filtering

## Monitoring

### Session Statistics

The system provides real-time statistics:

```python
{
    'total_sessions': 1000,
    'active_sessions': 150,
    'closed_sessions': 850,
    'sessions_with_duration': 800,
    'sessions_without_duration': 50
}
```

### Logging

Session events are logged for debugging:

- Session creation
- Session closure
- Duration calculation
- Timeout detection

## Troubleshooting

### Common Issues

1. **Sessions not closing automatically**
   - Check middleware is enabled in Django settings
   - Verify timeout configuration
   - Check for signal registration errors

2. **Durations not calculated**
   - Ensure signals are properly registered
   - Check for database constraint violations
   - Verify timezone settings

3. **Performance issues**
   - Monitor session count growth
   - Run cleanup command regularly
   - Consider adding database indexes

### Debug Commands

```bash
# Check session status
python manage.py shell
>>> from analytics.models import Session
>>> Session.objects.filter(end_time__isnull=True).count()  # Active sessions
>>> Session.objects.filter(duration__isnull=True).count()  # Missing durations

# Test utility functions
>>> from analytics.utils import get_session_stats
>>> get_session_stats()
```

## Future Enhancements

1. **Configurable timeout periods** per user/visitor type
2. **Session activity tracking** to extend timeouts
3. **Automatic cleanup scheduling** via cron/celery
4. **Session analytics dashboard** with charts and metrics
5. **Export functionality** for session data analysis

## Dependencies

- Django 3.2+
- Python 3.8+
- PostgreSQL (recommended for production)

## Security Considerations

- Session IDs are UUIDs for uniqueness
- IP addresses are stored for visitor tracking
- User authentication status is tracked
- No sensitive data is stored in sessions
