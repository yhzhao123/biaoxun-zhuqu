"""
DynamicSpider - Generic dynamic crawler based on CrawlSource configuration

This spider can crawl arbitrary tender websites based on CSS selectors,
URL patterns, and other configuration stored in CrawlSource model.

Features:
- Multiple extraction strategies: Intelligent, LLM, CSS Selectors
- Automatic page structure analysis
- Fallback chain for robust extraction
"""

import re
import logging
from datetime import datetime
from typing import Optional, Dict, List, Any
from urllib.parse import urljoin, urlparse
from decimal import Decimal, InvalidOperation

from bs4 import BeautifulSoup
import requests

from apps.crawler.spiders.base import BaseSpider
from apps.tenders.models import TenderNotice
from apps.crawler.extractors import ExtractionPipeline, ExtractionResult

logger = logging.getLogger(__name__)


class DynamicSpider(BaseSpider):
    """
    Generic dynamic spider that crawls websites based on CrawlSource configuration.

    Features:
    - Multiple extraction strategies with fallback chain
    - Intelligent extraction (auto-detect page structure)
    - LLM-based extraction (use configured LLM to parse content)
    - CSS selector-based extraction (fallback)
    - Pagination support with URL pattern
    - TenderNotice creation and storage
    - Keyword search capability
    - Multiple date format parsing
    - Budget amount parsing with currency conversion

    Extraction Priority:
    1. Intelligent extraction (analyze page structure automatically)
    2. LLM extraction (use AI to parse content)
    3. CSS selectors (configured in CrawlSource)
    """

    name = 'dynamic_spider'

    def __init__(self, crawl_source, use_llm: bool = True, use_intelligent: bool = True, **kwargs):
        """
        Initialize DynamicSpider with CrawlSource configuration.

        Args:
            crawl_source: CrawlSource model instance
            use_llm: Enable LLM-based extraction (default: True)
            use_intelligent: Enable intelligent extraction (default: True)
            **kwargs: Additional arguments for BaseSpider
        """
        # Extract configuration from CrawlSource
        min_delay = crawl_source.delay_seconds or 1.0
        max_delay = min_delay * 2

        super().__init__(
            min_delay=min_delay,
            max_delay=max_delay,
            **kwargs
        )

        self.crawl_source = crawl_source
        self.base_url = crawl_source.base_url
        self.delay_seconds = crawl_source.delay_seconds or 1

        # CSS selectors (fallback)
        self.selector_title = crawl_source.selector_title or 'h1, .title'
        self.selector_content = crawl_source.selector_content or '.content, article'
        self.selector_publish_date = crawl_source.selector_publish_date or '.date, time'
        self.selector_tenderer = crawl_source.selector_tenderer or '.tenderer, .buyer'
        self.selector_budget = crawl_source.selector_budget or '.budget, .amount'

        # URL pattern for pagination
        self.list_url_pattern = crawl_source.list_url_pattern or ''

        # Initialize extraction pipeline
        self.extraction_pipeline = ExtractionPipeline(
            use_llm=use_llm,
            use_intelligent=use_intelligent
        )

        # Log extraction mode
        extraction_modes = []
        if use_intelligent:
            extraction_modes.append('intelligent')
        if use_llm:
            extraction_modes.append('llm')
        extraction_modes.append('selector')
        logger.info(f"DynamicSpider initialized with extraction modes: {' -> '.join(extraction_modes)}")

    def extract_with_selector(self, html: str, selector: str) -> str:
        """
        Extract content from HTML using CSS selector.

        Args:
            html: HTML content string
            selector: CSS selector

        Returns:
            Extracted text content
        """
        if not html or not selector:
            return ''

        try:
            soup = BeautifulSoup(html, 'html.parser')

            # Try multiple selectors separated by comma (fallback)
            selectors = [s.strip() for s in selector.split(',')]

            for sel in selectors:
                elements = soup.select(sel)
                if elements:
                    # Get text content, strip whitespace
                    text = elements[0].get_text(strip=True)
                    if text:
                        return text

            return ''
        except Exception as e:
            logger.warning(f"Error extracting with selector '{selector}': {e}")
            return ''

    def extract_all_with_selector(self, html: str, selector: str) -> List[str]:
        """
        Extract all matching elements from HTML.

        Args:
            html: HTML content string
            selector: CSS selector

        Returns:
            List of extracted text contents
        """
        if not html or not selector:
            return []

        try:
            soup = BeautifulSoup(html, 'html.parser')
            elements = soup.select(selector)
            return [el.get_text(strip=True) for el in elements if el.get_text(strip=True)]
        except Exception as e:
            logger.warning(f"Error extracting all with selector '{selector}': {e}")
            return []

    def generate_list_urls(self, max_pages: int = 1) -> List[str]:
        """
        Generate list page URLs for pagination.

        Args:
            max_pages: Maximum number of pages to generate

        Returns:
            List of URLs
        """
        if not self.list_url_pattern:
            # No pagination, just return base URL
            return [self.base_url]

        urls = []
        for page in range(1, max_pages + 1):
            url = self.list_url_pattern.format(page=page)
            full_url = urljoin(self.base_url, url)
            urls.append(full_url)

        return urls

    def generate_detail_url(self, path: str) -> str:
        """
        Generate full detail page URL from relative path.

        Args:
            path: Relative or absolute URL path

        Returns:
            Full URL
        """
        if not path:
            return ''

        # Already absolute URL
        if path.startswith('http://') or path.startswith('https://'):
            return path

        return urljoin(self.base_url, path)

    def parse_date(self, date_str: str) -> Optional[datetime]:
        """
        Parse date string from various formats.

        Supports:
        - Chinese format: 2024年01月15日
        - ISO format: 2024-01-15
        - Slash format: 2024/01/15
        - With time: 2024-01-15 10:30:00

        Args:
            date_str: Date string to parse

        Returns:
            datetime object or None if parsing fails
        """
        if not date_str:
            return None

        from datetime import datetime

        date_str = date_str.strip()

        # Chinese format: 2024年01月15日 or 2024年1月15日
        match = re.match(r'(\d{4})年(\d{1,2})月(\d{1,2})日', date_str)
        if match:
            year, month, day = match.groups()
            try:
                return datetime(int(year), int(month), int(day))
            except ValueError:
                pass

        # Try common formats
        formats = [
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d',
            '%Y/%m/%d',
            '%Y.%m.%d',
            '%d/%m/%Y',
            '%m/%d/%Y',
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue

        logger.warning(f"Could not parse date: {date_str}")
        return None

    def parse_budget(self, budget_str: str) -> Optional[Decimal]:
        """
        Parse budget string and convert to decimal.

        Supports:
        - Plain numbers: 100000
        - With currency: 100万元, 100万, $100,000
        - Chinese units: 100万元, 100万, 100亿

        Args:
            budget_str: Budget string to parse

        Returns:
            Decimal amount or None if parsing fails
        """
        if not budget_str:
            return None

        budget_str = budget_str.strip()

        # Remove common currency symbols and whitespace
        # Also remove common prefixes like "人民币", "RMB", etc.
        budget_str = (budget_str
            .replace('¥', '')
            .replace('$', '')
            .replace('€', '')
            .replace('人民币', '')
            .replace('RMB', '')
            .replace('美元', '')
            .replace('欧元', '')
            .strip())

        # First try to match number with unit (e.g., 100万, 100万元, 100亿)
        # Match patterns like: 100万, 100万元, 100亿, 100.5万
        match = re.match(r'([\d,\.]+)\s*(亿|万|千|万元|亿元)?', budget_str)
        if match:
            try:
                number_str = match.group(1).replace(',', '')
                number = Decimal(number_str)
                unit = match.group(2)

                # Convert units to base (yuan)
                if unit in ('亿', '亿元'):
                    number = number * Decimal('100000000')
                elif unit in ('万', '万元'):
                    number = number * Decimal('10000')
                elif unit == '千':
                    number = number * Decimal('1000')

                return number
            except (InvalidOperation, ValueError) as e:
                logger.warning(f"Error parsing budget '{budget_str}': {e}")
                return None

        # Try plain number
        try:
            clean_str = re.sub(r'[^\d.]', '', budget_str)
            if clean_str:
                return Decimal(clean_str)
        except InvalidOperation:
            pass

        return None

    def crawl(self, max_pages: int = 1) -> List[Dict[str, Any]]:
        """
        Execute the crawl operation.

        Args:
            max_pages: Maximum number of list pages to crawl

        Returns:
            List of crawled items
        """
        items = []

        list_urls = self.generate_list_urls(max_pages)

        for list_url in list_urls:
            try:
                response = self.fetch(list_url)
                list_items = self.parse_list(response.text)

                for item in list_items:
                    detail_url = item.get('url')
                    if detail_url:
                        try:
                            detail_response = self.fetch(detail_url)
                            notice_data = self.parse_detail(
                                detail_response.text,
                                source_url=detail_url
                            )
                            if notice_data:
                                notice = self.create_tender_notice(notice_data)
                                if notice:
                                    items.append({
                                        'notice_id': notice.notice_id,
                                        'title': notice.title,
                                        'source_url': notice.source_url
                                    })
                        except Exception as e:
                            logger.error(f"Error crawling detail {detail_url}: {e}")
                            continue
            except Exception as e:
                logger.error(f"Error crawling list {list_url}: {e}")
                continue

        return items

    def parse_list(self, html: str) -> List[Dict[str, Any]]:
        """
        Parse list page to extract item links.

        Args:
            html: List page HTML content

        Returns:
            List of item dictionaries with 'url' key
        """
        items = []

        try:
            soup = BeautifulSoup(html, 'html.parser')

            # Find all links that might be detail pages
            # This is a generic approach - can be customized
            links = soup.select('a[href]')

            for link in links:
                href = link.get('href', '')
                text = link.get_text(strip=True)

                # Skip empty or navigation links
                if not href or not text:
                    continue

                # Skip javascript: and other non-http links
                if href.startswith('javascript:') or href.startswith('#'):
                    continue

                # Skip likely navigation links
                skip_patterns = ['/index', '/home', '/about', '/contact', '/news']
                if any(pattern in href.lower() for pattern in skip_patterns):
                    continue

                full_url = self.generate_detail_url(href)

                # Only include http/https URLs
                if not full_url.startswith(('http://', 'https://')):
                    continue

                items.append({
                    'url': full_url,
                    'title': text
                })

        except Exception as e:
            logger.error(f"Error parsing list: {e}")

        return items

    def parse_detail(self, html: str, source_url: str = '') -> Optional[Dict[str, Any]]:
        """
        Parse detail page to extract tender information.

        Uses multiple extraction strategies with fallback chain:
        1. Intelligent extraction (auto-detect page structure)
        2. LLM extraction (AI-powered parsing)
        3. CSS selectors (configured in CrawlSource)

        Args:
            html: Detail page HTML content
            source_url: Source URL of the page

        Returns:
            Dictionary with extracted data
        """
        try:
            # Prepare selectors for fallback
            selectors = {
                'title': self.selector_title,
                'content': self.selector_content,
                'publish_date': self.selector_publish_date,
                'tenderer': self.selector_tenderer,
                'budget': self.selector_budget,
            }

            # Use extraction pipeline
            extraction_result = self.extraction_pipeline.extract(
                html=html,
                selectors=selectors,
                source_url=source_url
            )

            # Log extraction method used
            logger.info(f"Extraction method: {extraction_result.extraction_method}, "
                       f"confidence: {extraction_result.confidence:.2f}")

            # Build result dictionary from extraction result
            result = {
                'title': extraction_result.title,
                'description': extraction_result.description,
                'tenderer': extraction_result.tenderer,
                'publish_date': extraction_result.publish_date,
                'budget': extraction_result.budget,
                'source_url': source_url,
                'notice_type': 'bidding',  # Default, can be inferred from content
                'extraction_method': extraction_result.extraction_method,
                'extraction_confidence': extraction_result.confidence,
            }

            # Get additional data from extraction result
            if extraction_result.data:
                result['project_number'] = extraction_result.data.get('project_number')
                result['region'] = extraction_result.data.get('region')
                result['industry'] = extraction_result.data.get('industry')

            # Determine notice type from content
            title = result.get('title') or ''
            description = result.get('description') or ''
            if '中标' in title or '中标' in description or '成交' in title or '成交' in description:
                result['notice_type'] = 'win'

            return result

        except Exception as e:
            logger.error(f"Error parsing detail page {source_url}: {e}")
            return None

    def create_tender_notice(self, data: Dict[str, Any]) -> Optional[TenderNotice]:
        """
        Create TenderNotice from extracted data.

        Args:
            data: Dictionary with tender information

        Returns:
            Created TenderNotice instance or None
        """
        try:
            title = data.get('title', '').strip() if data.get('title') else ''
            source_url = data.get('source_url', '').strip() if data.get('source_url') else ''

            if not title or not source_url:
                logger.warning("Missing required fields: title or source_url")
                return None

            # Check for existing notice with same source_url
            existing = TenderNotice.objects.filter(source_url=source_url).first()
            if existing:
                logger.info(f"Notice already exists for {source_url}")
                return existing

            # Determine notice type from content
            # Check title and description for "中标" or "WIN" keyword
            notice_type = data.get('notice_type', 'bidding')
            description = data.get('description', '') or ''

            if notice_type == 'bidding':
                # Try to detect win notice from content
                # Check for Chinese "中标" or English "WIN" keyword
                if '中标' in title or '中标' in description or 'WIN' in title or 'WIN' in description or '成交' in title or '成交' in description:
                    notice_type = 'win'

            # Generate notice_id
            from django.utils.text import slugify
            import uuid
            notice_id = f"{slugify(title)[:30]}-{uuid.uuid4().hex[:8]}"

            # Prepare fields
            create_kwargs = {
                'notice_id': notice_id,
                'title': title,
                'description': description,
                'tenderer': data.get('tenderer', '') or '',
                'budget': data.get('budget'),
                'budget_amount': data.get('budget'),  # Use same value for now
                'publish_date': data.get('publish_date'),
                'source_url': source_url,
                'source_site': self.crawl_source.name,
                'notice_type': notice_type,
                'status': 'active'
            }

            # Add optional fields if available
            if data.get('project_number'):
                create_kwargs['project_number'] = data.get('project_number')
            if data.get('region'):
                create_kwargs['region'] = data.get('region')
            if data.get('industry'):
                create_kwargs['industry'] = data.get('industry')

            notice = TenderNotice.objects.create(**create_kwargs)

            # Log extraction method used
            extraction_method = data.get('extraction_method', 'unknown')
            confidence = data.get('extraction_confidence', 0)
            logger.info(f"Created TenderNotice: {notice.notice_id} "
                       f"(method: {extraction_method}, confidence: {confidence:.2f})")
            return notice

        except Exception as e:
            logger.error(f"Error creating TenderNotice: {e}")
            return None

    def search_notices(self, keyword: str, limit: int = 50) -> List[TenderNotice]:
        """
        Search TenderNotice by keyword.

        Args:
            keyword: Search keyword
            limit: Maximum number of results

        Returns:
            List of matching TenderNotice instances
        """
        if not keyword:
            return []

        from django.db.models import Q

        try:
            notices = TenderNotice.objects.filter(
                Q(title__icontains=keyword) |
                Q(description__icontains=keyword) |
                Q(tenderer__icontains=keyword) |
                Q(project_name__icontains=keyword)
            )[:limit]

            return list(notices)
        except Exception as e:
            logger.error(f"Error searching notices: {e}")
            return []