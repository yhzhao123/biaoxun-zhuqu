"""
Tenders App Configuration
"""
from django.apps import AppConfig


class TendersConfig(AppConfig):
    """Tenders application configuration"""
    name = 'apps.tenders'
    verbose_name = '招标公告'

    def ready(self):
        """Initialize signals when app is ready"""
        import apps.tenders.signals  # noqa
