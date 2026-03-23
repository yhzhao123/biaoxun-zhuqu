"""
Test TenderNotice model - Phase 2 Task 006
TDD: RED state - tests should fail until model is implemented
"""
import pytest
from django.test import TestCase
from django.db import IntegrityError
from django.utils import timezone


@pytest.mark.django_db
class TestTenderNoticeModel(TestCase):
    """Test TenderNotice model fields and constraints."""

    def test_model_exists(self):
        """Test that TenderNotice model exists in tenders app."""
        from apps.tenders.models import TenderNotice
        assert TenderNotice is not None

    def test_required_fields_exist(self):
        """Test that TenderNotice has required fields: notice_id, title, tenderer."""
        from apps.tenders.models import TenderNotice

        # Get all field names
        field_names = [f.name for f in TenderNotice._meta.get_fields()]

        # Required fields according to BDD scenario
        assert 'notice_id' in field_names, "notice_id field should exist"
        assert 'title' in field_names, "title field should exist"
        assert 'tenderer' in field_names, "tenderer field should exist"

    def test_notice_id_unique_constraint(self):
        """Test that notice_id has unique constraint."""
        from apps.tenders.models import TenderNotice

        # Get notice_id field and check unique
        notice_id_field = TenderNotice._meta.get_field('notice_id')
        assert notice_id_field.unique is True, "notice_id should have unique constraint"

    def test_notice_id_unique_raises_error(self):
        """Test that duplicate notice_id raises IntegrityError."""
        from apps.tenders.models import TenderNotice

        # Create first tender notice
        TenderNotice.objects.create(
            notice_id='TEST-001',
            title='Test Tender 1',
            tenderer='Test Company'
        )

        # Attempt to create duplicate should raise IntegrityError
        with pytest.raises(IntegrityError):
            TenderNotice.objects.create(
                notice_id='TEST-001',  # Same notice_id
                title='Test Tender 2',
                tenderer='Another Company'
            )

    def test_status_field_choices(self):
        """Test that status field has correct choices."""
        from apps.tenders.models import TenderNotice

        status_field = TenderNotice._meta.get_field('status')
        valid_choices = [choice[0] for choice in status_field.choices]

        # Should have pending, active, closed, expired choices
        assert 'pending' in valid_choices, "status should have 'pending' choice"
        assert 'active' in valid_choices, "status should have 'active' choice"
        assert 'closed' in valid_choices, "status should have 'closed' choice"
        assert 'expired' in valid_choices, "status should have 'expired' choice"

    def test_default_values(self):
        """Test default values: currency='CNY', status='pending'."""
        from apps.tenders.models import TenderNotice

        # Create tender notice with minimal required fields
        tender = TenderNotice.objects.create(
            notice_id='TEST-DEFAULT-001',
            title='Default Test',
            tenderer='Test Company'
        )

        # Check default values
        assert tender.currency == 'CNY', "Default currency should be 'CNY'"
        assert tender.status == 'pending', "Default status should be 'pending'"

    def test_str_method(self):
        """Test __str__ method returns meaningful representation."""
        from apps.tenders.models import TenderNotice

        tender = TenderNotice(
            notice_id='TEST-STR-001',
            title='招标公告测试标题',
            tenderer='测试招标人'
        )

        # __str__ should return title or meaningful representation
        str_repr = str(tender)
        assert len(str_repr) > 0, "__str__ should return non-empty string"
        assert 'TEST-STR-001' in str_repr or '招标公告测试标题' in str_repr, \
            "__str__ should contain notice_id or title"

    def test_all_fields_exist(self):
        """Test that all required fields exist in the model."""
        from apps.tenders.models import TenderNotice

        expected_fields = [
            'notice_id', 'title', 'description', 'tenderer', 'budget',
            'currency', 'publish_date', 'deadline_date', 'region',
            'industry', 'source_url', 'source_site', 'status',
            'ai_summary', 'ai_keywords', 'ai_category',
            'relevance_score', 'crawl_batch_id'
        ]

        field_names = [f.name for f in TenderNotice._meta.get_fields()]

        for field in expected_fields:
            assert field in field_names, f"Field '{field}' should exist"

    def test_bdd_scenario_data_extraction(self):
        """
        BDD Scenario: 成功爬取政府采购网信息
        Given 爬虫任务已配置
        When 爬虫启动
        Then 所有提取的数据应包含title、notice_id、tenderer字段
        """
        from apps.tenders.models import TenderNotice

        # Simulate crawled data
        crawled_data = {
            'notice_id': 'GOV-2024-001',
            'title': '某省政府采购项目招标公告',
            'tenderer': '某省政府采购中心',
            'budget': 1000000.00,
            'currency': 'CNY',
            'region': '北京',
            'industry': 'IT服务',
            'source_url': 'https://www.ccgp.gov.cn/',
            'source_site': '中国政府采购网',
            'status': 'active'
        }

        # Create tender from crawled data
        tender = TenderNotice.objects.create(**crawled_data)

        # Verify all required fields are present
        assert tender.title == crawled_data['title']
        assert tender.notice_id == crawled_data['notice_id']
        assert tender.tenderer == crawled_data['tenderer']

    def test_publish_date_and_deadline_date_fields(self):
        """Test publish_date and deadline_date fields exist and work."""
        from apps.tenders.models import TenderNotice

        now = timezone.now()
        deadline = now + timezone.timedelta(days=30)

        tender = TenderNotice.objects.create(
            notice_id='TEST-DATE-001',
            title='日期测试',
            tenderer='测试公司',
            publish_date=now,
            deadline_date=deadline
        )

        assert tender.publish_date is not None
        assert tender.deadline_date is not None
        assert tender.deadline_date > tender.publish_date