from django.apps import AppConfig


class MetricsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'metrics'
    verbose_name = 'Metrics and Monitoring'
    
    def ready(self):
        """Import and register signals when the app is ready"""
        try:
            import metrics.signals
        except ImportError:
            pass
