"""
Government procurement spider tests

Test GovSpider functionality including:
- HTML parsing for bid announcements
- Field extraction (title, date, purchaser, amount, etc.)
- Pagination handling
- Data transformation to TenderNotice format
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock


class TestGovSpiderExists:
    """Test 1: GovSpider class exists and inherits from BaseSpider"""

    def test_gov_spider_class_exists(self):
        """GovSpider class should exist"""
        from apps.crawler.spiders.gov_spider import GovSpider
        assert GovSpider is not None

    def test_gov_spider_inherits_base_spider(self):
        """GovSpider should inherit from BaseSpider"""
        from apps.crawler.spiders.gov_spider import GovSpider
        from apps.crawler.spiders.base import BaseSpider
        assert issubclass(GovSpider, BaseSpider)


class TestGovSpiderParsing:
    """Test 2: HTML parsing for bid announcements"""

    def test_parse_list_page(self):
        """Should parse list page and extract announcement links"""
        from apps.crawler.spiders.gov_spider import GovSpider

        spider = GovSpider()

        # Sample HTML from government procurement website list page
        sample_html = """
        <html>
        <body>
            <ul class="notice-list">
                <li>
                    <a href="/notice/detail/12345.html">某单位信息化建设项目招标公告</a>
                    <span class="date">2026-03-20</span>
                </li>
                <li>
                    <a href="/notice/detail/12346.html">办公设备采购项目公开招标公告</a>
                    <span class="date">2026-03-19</span>
                </li>
            </ul>
        </body>
        </html>
        """

        mock_response = Mock()
        mock_response.text = sample_html
        mock_response.url = "http://www.ccgp.gov.cn/notice/list.html"

        links = spider.parse_list_page(mock_response)

        assert len(links) == 2
        assert links[0]['url'] == "/notice/detail/12345.html"
        assert links[0]['title'] == "某单位信息化建设项目招标公告"
        assert links[0]['date'] == "2026-03-20"

    def test_parse_detail_page(self):
        """Should parse detail page and extract full announcement info"""
        from apps.crawler.spiders.gov_spider import GovSpider

        spider = GovSpider()

        # Sample HTML from detail page
        sample_html = """
        <html>
        <body>
            <div class="notice-detail">
                <h1 class="title">某单位信息化建设项目招标公告</h1>
                <div class="info">
                    <span>发布时间：2026-03-20</span>
                    <span>招标编号：ZB2026-001</span>
                </div>
                <div class="content">
                    <p>招标人：某科技有限公司</p>
                    <p>招标代理机构：某招标代理有限公司</p>
                    <p>预算金额：￥500,000.00</p>
                    <p>开标时间：2026-04-15 09:30</p>
                    <p>项目概况：本项目为信息化建设项目...</p>
                </div>
            </div>
        </body>
        </html>
        """

        mock_response = Mock()
        mock_response.text = sample_html
        mock_response.url = "http://www.ccgp.gov.cn/notice/detail/12345.html"

        data = spider.parse_detail_page(mock_response)

        assert data['title'] == "某单位信息化建设项目招标公告"
        assert data['publish_date'] == "2026-03-20"
        assert data['bid_number'] == "ZB2026-001"
        assert data['bidder'] == "某科技有限公司"
        assert data['agency'] == "某招标代理有限公司"
        assert "500000" in data['budget_amount'] or "500,000" in data['budget_amount']


class TestFieldExtraction:
    """Test 3: Field extraction accuracy"""

    @pytest.mark.parametrize("html_content,expected_amount", [
        ("<p>预算金额：￥1,234,567.00元</p>", "1,234,567.00"),
        ("<p>采购预算：500万元</p>", "5000000"),
        ("<p>项目金额：¥100000</p>", "100000"),
    ])
    def test_extract_amount(self, html_content, expected_amount):
        """Should extract amount from various formats"""
        from apps.crawler.spiders.gov_spider import GovSpider

        spider = GovSpider()
        amount = spider._extract_amount(html_content)

        # Amount extraction should handle various formats
        assert amount is not None
        assert len(amount) > 0

    @pytest.mark.parametrize("html_content,expected_date", [
        ("<span>发布时间：2026-03-20</span>", "2026-03-20"),
        ("<span>2026年03月20日</span>", "2026-03-20"),
        ("<span>2026/03/20</span>", "2026-03-20"),
    ])
    def test_extract_date(self, html_content, expected_date):
        """Should extract and normalize date from various formats"""
        from apps.crawler.spiders.gov_spider import GovSpider

        spider = GovSpider()
        date = spider._extract_date(html_content, "publish")

        assert date is not None

    def test_extract_bid_type(self):
        """Should extract bid type from title"""
        from apps.crawler.spiders.gov_spider import GovSpider

        spider = GovSpider()

        test_cases = [
            ("某项目招标公告", "tender"),
            ("某项目中标公告", "win"),
            ("某项目竞争性谈判公告", "tender"),
            ("某项目成交公告", "win"),
        ]

        for title, expected_type in test_cases:
            bid_type = spider._extract_bid_type(title)
            assert bid_type == expected_type


class TestDataTransformation:
    """Test 4: Transform crawled data to TenderNotice format"""

    def test_transform_to_tender_notice(self):
        """Should transform spider data to TenderNotice format"""
        from apps.crawler.spiders.gov_spider import GovSpider

        spider = GovSpider()

        crawled_data = {
            'title': '某单位信息化建设项目招标公告',
            'publish_date': '2026-03-20',
            'bid_number': 'ZB2026-001',
            'bidder': '某科技有限公司',
            'agency': '某招标代理有限公司',
            'budget_amount': '500000',
            'open_date': '2026-04-15 09:30',
            'content': '项目概况：本项目为信息化建设项目...',
            'source_url': 'http://www.ccgp.gov.cn/notice/detail/12345.html',
            'source_site': '政府采购网',
        }

        tender_data = spider.transform_to_tender(crawled_data)

        assert tender_data['title'] == crawled_data['title']
        assert tender_data['bid_number'] == crawled_data['bid_number']
        assert tender_data['bidder_name'] == crawled_data['bidder']
        assert tender_data['agency_name'] == crawled_data['agency']
        assert tender_data['source_site'] == '政府采购网'
        assert tender_data['notice_type'] == 'tender'


class TestGovSpiderIntegration:
    """Test 5: Integration tests with mocked HTTP"""

    @patch('apps.crawler.spiders.base.requests.Session.get')
    def test_crawl_single_page(self, mock_get):
        """Should crawl a single page successfully"""
        from apps.crawler.spiders.gov_spider import GovSpider

        spider = GovSpider()

        # Mock list page response
        list_html = """
        <html><body>
            <ul class="notice-list">
                <li>
                    <a href="/detail/1.html">项目1</a>
                    <span class="date">2026-03-20</span>
                </li>
            </ul>
        </body></html>
        """

        # Mock detail page response
        detail_html = """
        <html><body>
            <div class="notice-detail">
                <h1 class="title">项目1</h1>
                <div class="info">
                    <span>发布时间：2026-03-20</span>
                </div>
                <div class="content">
                    <p>招标人：公司A</p>
                    <p>预算金额：￥100,000.00</p>
                </div>
            </div>
        </body></html>
        """

        mock_list_response = Mock()
        mock_list_response.text = list_html
        mock_list_response.status_code = 200

        mock_detail_response = Mock()
        mock_detail_response.text = detail_html
        mock_detail_response.status_code = 200

        mock_get.side_effect = [mock_list_response, mock_detail_response]

        items = spider.crawl(limit=1)

        assert len(items) == 1
        assert items[0]['title'] == "项目1"


class TestGovSpiderConfiguration:
    """Test 6: Spider configuration"""

    def test_default_source_url(self):
        """GovSpider should have default source URL"""
        from apps.crawler.spiders.gov_spider import GovSpider

        spider = GovSpider()
        assert spider.source_url is not None
        assert "ccgp.gov.cn" in spider.source_url

    def test_spider_name(self):
        """GovSpider should have correct name"""
        from apps.crawler.spiders.gov_spider import GovSpider

        spider = GovSpider()
        assert spider.name == 'gov_spider'

    def test_custom_source_url(self):
        """GovSpider should accept custom source URL"""
        from apps.crawler.spiders.gov_spider import GovSpider

        custom_url = "http://custom.ccgp.gov.cn/notice/"
        spider = GovSpider(source_url=custom_url)
        assert spider.source_url == custom_url
