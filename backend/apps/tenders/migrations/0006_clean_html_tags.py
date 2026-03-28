# Generated manually: Clean HTML tags from existing tender data

from django.db import migrations
from django.db.models import Q
import re


def clean_html_tags(text):
    """Remove HTML tags from text using regex."""
    if not text:
        return text
    # Remove HTML tags
    clean = re.sub(r'<[^>]+>', '', str(text))
    # Strip whitespace
    return clean.strip()


def clean_existing_tender_data(apps, schema_editor):
    """
    Clean HTML tags from existing TenderNotice records.
    This migration removes HTML tags (like <font>, <div>, etc.) from
    title, description, tenderer, region, and industry fields.
    """
    TenderNotice = apps.get_model('tenders', 'TenderNotice')

    # Find records that might contain HTML tags (containing '<' and '>')
    records_to_clean = TenderNotice.objects.filter(
        Q(title__contains='<') | Q(title__contains='>') |
        Q(description__contains='<') | Q(description__contains='>') |
        Q(tenderer__contains='<') | Q(tenderer__contains='>') |
        Q(region__contains='<') | Q(region__contains='>') |
        Q(industry__contains='<') | Q(industry__contains='>')
    )

    cleaned_count = 0
    for record in records_to_clean:
        # Clean HTML from all text fields
        record.title = clean_html_tags(record.title)
        record.description = clean_html_tags(record.description)
        record.tenderer = clean_html_tags(record.tenderer)
        record.region = clean_html_tags(record.region)
        record.industry = clean_html_tags(record.industry)
        record.save(update_fields=['title', 'description', 'tenderer', 'region', 'industry'])
        cleaned_count += 1

    print(f"Cleaned HTML tags from {cleaned_count} TenderNotice records")


def reverse_migration(apps, schema_editor):
    """
    Reverse migration - no-op since we can't restore original HTML.
    """
    pass


class Migration(migrations.Migration):
    """
    Data migration: Clean HTML tags from existing tender data.

    This migration removes HTML formatting tags (like <font color='...'>, <div>, etc.)
    from all text fields in TenderNotice model to prevent display issues in the frontend.
    """

    dependencies = [
        ('tenders', '0005_rename_tender_title_pub_idx_tender_title_date_idx_and_more'),
    ]

    operations = [
        migrations.RunPython(clean_existing_tender_data, reverse_migration),
    ]
