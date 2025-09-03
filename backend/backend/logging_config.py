"""
Enhanced logging configuration for ELK stack integration
"""
import json
import logging
import sys
from datetime import datetime
from django.conf import settings


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""
    
    def format(self, record):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'thread': record.thread,
            'process': record.process,
        }
        
        # Add extra fields if present
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        if hasattr(record, 'session_id'):
            log_entry['session_id'] = record.session_id
        if hasattr(record, 'ip_address'):
            log_entry['ip_address'] = record.ip_address
        if hasattr(record, 'user_agent'):
            log_entry['user_agent'] = record.user_agent
        if hasattr(record, 'method'):
            log_entry['method'] = record.method
        if hasattr(record, 'path'):
            log_entry['path'] = record.path
        if hasattr(record, 'status_code'):
            log_entry['status_code'] = record.status_code
        if hasattr(record, 'response_time'):
            log_entry['response_time'] = record.response_time
        if hasattr(record, 'error_type'):
            log_entry['error_type'] = record.error_type
        if hasattr(record, 'error_message'):
            log_entry['error_message'] = record.error_message
            
        # Add environment info
        log_entry['environment'] = getattr(settings, 'DJANGO_ENV', 'development')
        log_entry['project'] = 'fauxdan'
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
            
        return json.dumps(log_entry)


class RequestContextFilter(logging.Filter):
    """Filter to add request context to log records"""
    
    def filter(self, record):
        # Try to get request from thread local storage
        try:
            from django.utils.deprecation import MiddlewareMixin
            from threading import local
            
            # This would be set by middleware
            if hasattr(self, '_request'):
                request = self._request
                if request:
                    record.method = getattr(request, 'method', '')
                    record.path = getattr(request, 'path', '')
                    record.ip_address = self._get_client_ip(request)
                    record.user_agent = request.META.get('HTTP_USER_AGENT', '')
                    
                    # Add user info if authenticated
                    if hasattr(request, 'user') and request.user.is_authenticated:
                        record.user_id = request.user.id
                        
        except Exception:
            pass
            
        return True
    
    def _get_client_ip(self, request):
        """Get client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


def get_logging_config():
    """Get enhanced logging configuration for ELK stack"""
    import os
    
    # Ensure log directory exists
    log_dir = '/var/log/app'
    if not os.path.exists(log_dir):
        try:
            os.makedirs(log_dir, exist_ok=True)
        except (OSError, PermissionError):
            # If we can't create the directory, fall back to console-only logging
            return {
                'version': 1,
                'disable_existing_loggers': False,
                'formatters': {
                    'json': {
                        '()': JSONFormatter,
                    },
                },
                'filters': {
                    'request_context': {
                        '()': RequestContextFilter,
                    },
                },
                'handlers': {
                    'console': {
                        'class': 'logging.StreamHandler',
                        'formatter': 'json',
                        'filters': ['request_context'],
                        'stream': sys.stdout,
                    },
                },
                'root': {
                    'handlers': ['console'],
                    'level': 'INFO',
                },
                'loggers': {
                    'django': {
                        'handlers': ['console'],
                        'level': 'INFO',
                        'propagate': False,
                    },
                    'django.request': {
                        'handlers': ['console'],
                        'level': 'ERROR',
                        'propagate': False,
                    },
                    'django.db.backends': {
                        'handlers': ['console'],
                        'level': 'WARNING',
                        'propagate': False,
                    },
                    'analytics': {
                        'handlers': ['console'],
                        'level': 'DEBUG',
                        'propagate': False,
                    },
                    'metrics': {
                        'handlers': ['console'],
                        'level': 'DEBUG',
                        'propagate': False,
                    },
                    'internet': {
                        'handlers': ['console'],
                        'level': 'DEBUG',
                        'propagate': False,
                    },
                    'fauxdan': {
                        'handlers': ['console'],
                        'level': 'DEBUG',
                        'propagate': False,
                    },
                },
            }
    
    return {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'json': {
                '()': JSONFormatter,
            },
            'verbose': {
                'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
                'style': '{',
            },
            'simple': {
                'format': '{levelname} {message}',
                'style': '{',
            },
        },
        'filters': {
            'request_context': {
                '()': RequestContextFilter,
            },
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'json',
                'filters': ['request_context'],
                'stream': sys.stdout,
            },
            'file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': '/var/log/app/django.log',
                'maxBytes': 1024*1024*15,  # 15MB
                'backupCount': 10,
                'formatter': 'json',
                'filters': ['request_context'],
            },
            'error_file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': '/var/log/app/django-error.log',
                'maxBytes': 1024*1024*15,  # 15MB
                'backupCount': 10,
                'formatter': 'json',
                'filters': ['request_context'],
                'level': 'ERROR',
            },
        },
        'root': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'loggers': {
            'django': {
                'handlers': ['console', 'file'],
                'level': 'INFO',
                'propagate': False,
            },
            'django.request': {
                'handlers': ['console', 'error_file'],
                'level': 'ERROR',
                'propagate': False,
            },
            'django.db.backends': {
                'handlers': ['console'],
                'level': 'WARNING',
                'propagate': False,
            },
            'analytics': {
                'handlers': ['console', 'file'],
                'level': 'DEBUG',
                'propagate': False,
            },
            'metrics': {
                'handlers': ['console', 'file'],
                'level': 'DEBUG',
                'propagate': False,
            },
            'internet': {
                'handlers': ['console', 'file'],
                'level': 'DEBUG',
                'propagate': False,
            },
            'fauxdan': {
                'handlers': ['console', 'file'],
                'level': 'DEBUG',
                'propagate': False,
            },
        },
    }
