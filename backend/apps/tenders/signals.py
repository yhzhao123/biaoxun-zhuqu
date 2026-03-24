"""
TenderNotice Signals - Phase 6 Task 031
Automatically update search_vector on save
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import connection

from .models import TenderNotice


@receiver(post_save, sender=TenderNotice)
def update_search_vector(sender, instance, created, **kwargs):
    """
    Update search_vector when TenderNotice is saved.

    Uses PostgreSQL to_tsvector for full-text search indexing.
    Skipped if not using PostgreSQL.
    """
    # Only update for PostgreSQL databases
    if connection.vendor != 'postgresql':
        return

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE tender_notices
                SET search_vector = (
                    setweight(to_tsvector('simple', COALESCE(title, '')), 'A') ||
                    setweight(to_tsvector('simple', COALESCE(description, '')), 'B') ||
                    setweight(to_tsvector('simple', COALESCE(tenderer, '')), 'C') ||
                    setweight(to_tsvector('simple', COALESCE(project_name, '')), 'C')
                )
                WHERE id = %s
            """, [instance.id])
    except Exception:
        # Log error but don't fail the save
        import logging
        logger = logging.getLogger(__name__)
        logger.exception("Failed to update search_vector")
