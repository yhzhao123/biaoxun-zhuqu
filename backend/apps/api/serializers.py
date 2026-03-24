"""
API Serializers - Phase 6
"""

from rest_framework import serializers
from apps.tenders.models import TenderNotice


class TenderSerializer(serializers.ModelSerializer):
    """招标公告序列化器"""

    class Meta:
        model = TenderNotice
        fields = [
            'id',
            'notice_id',
            'title',
            'description',
            'tenderer',
            'budget',
            'currency',
            'publish_date',
            'deadline_date',
            'region',
            'industry',
            'source_url',
            'source_site',
            'status',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
