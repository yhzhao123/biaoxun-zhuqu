"""
DynamicSpider - Generic dynamic crawler based on CrawlSource configuration

This spider can crawl arbitrary tender websites based on CSS selectors,
URL patterns, and other configuration stored in CrawlSource model.

Features:
- Multiple extraction modes: HTML, API, Intelligent, LLM, Auto
- API support for dynamically loaded websites
- Automatic page structure analysis
- Fallback chain for robust extraction
"""

import re
import json
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
    - Multiple extraction modes: HTML, API, Intelligent, LLM, Auto
    - API support for dynamically loaded websites (AJAX)
    - Intelligent extraction (auto-detect page structure)
    - LLM-based extraction (use configured LLM to parse content)
    - CSS selector-based extraction (fallback)
    - Pagination support with URL pattern
    - TenderNotice creation and storage

    Extraction Modes:
    - html: Parse HTML with CSS selectors
    - api: Call external API and parse JSON response
    - intelligent: Auto-detect page structure
    - llm: Use LLM to extract structured data
    - auto: Try intelligent -> llm -> html automatically
    """

    name = 'dynamic_spider'

    def __init__(self, crawl_source, **kwargs):
        """
        Initialize DynamicSpider with CrawlSource configuration.

        Args:
            crawl_source: CrawlSource model instance
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

        # Extraction mode
        self.extraction_mode = crawl_source.extraction_mode or 'auto'

        # CSS selectors (for HTML mode)
        self.selector_title = crawl_source.selector_title or 'h1, .title'
        self.selector_content = crawl_source.selector_content or '.content, article'
        self.selector_publish_date = crawl_source.selector_publish_date or '.date, time'
        self.selector_tenderer = crawl_source.selector_tenderer or '.tenderer, .buyer'
        self.selector_budget = crawl_source.selector_budget or '.budget, .amount'

        # List page selectors (for HTML mode)
        self.list_container_selector = getattr(crawl_source, 'list_container_selector', '') or ''
        self.list_item_selector = getattr(crawl_source, 'list_item_selector', '') or ''
        self.list_link_selector = getattr(crawl_source, 'list_link_selector', '') or ''

        # URL pattern for pagination
        self.list_url_pattern = crawl_source.list_url_pattern or ''

        # API configuration (for API mode)
        self.api_url = getattr(crawl_source, 'api_url', '') or ''
        self.api_method = getattr(crawl_source, 'api_method', 'POST') or 'POST'
        self.api_params = getattr(crawl_source, 'api_params', {}) or {}
        self.api_headers = getattr(crawl_source, 'api_headers', {}) or {}
        self.api_response_path = getattr(crawl_source, 'api_response_path', '') or ''

        # API field mappings
        self.api_field_title = getattr(crawl_source, 'api_field_title', '') or ''
        self.api_field_url = getattr(crawl_source, 'api_field_url', '') or ''
        self.api_field_date = getattr(crawl_source, 'api_field_date', '') or ''
        self.api_field_budget = getattr(crawl_source, 'api_field_budget', '') or ''
        self.api_field_tenderer = getattr(crawl_source, 'api_field_tenderer', '') or ''

        # Pagination config
        self.page_param_name = getattr(crawl_source, 'page_param_name', 'page') or 'page'
        self.page_start = getattr(crawl_source, 'page_start', 1) or 1
        self.max_pages = getattr(crawl_source, 'max_pages', 10) or 10

        # Initialize extraction pipeline for HTML/intelligent/LLM modes
        use_llm = self.extraction_mode in ('llm', 'auto')
        use_intelligent = self.extraction_mode in ('intelligent', 'auto')

        self.extraction_pipeline = ExtractionPipeline(
            use_llm=use_llm,
            use_intelligent=use_intelligent
        )

        # Log initialization
        logger.info(f"DynamicSpider initialized for {crawl_source.name}")
        logger.info(f"  Extraction mode: {self.extraction_mode}")
        if self.extraction_mode == 'api' or self.api_url:
            logger.info(f"  API URL: {self.api_url}")

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

    def crawl(self, max_pages: int = None) -> List[Dict[str, Any]]:
        """
        Execute the crawl operation.

        Supports multiple extraction modes:
        - api: Call external API and parse JSON response
        - html: Parse HTML with CSS selectors
        - intelligent: Auto-detect page structure
        - llm: Use LLM to extract structured data
        - auto: Try multiple methods automatically

        Args:
            max_pages: Maximum number of list pages to crawl (overrides config)

        Returns:
            List of crawled items
        """
        # Use configured max_pages if not specified
        if max_pages is None:
            max_pages = self.max_pages

        items = []

        # Determine extraction mode
        if self.extraction_mode == 'api' or (self.api_url and self.extraction_mode != 'html'):
            # API mode: Call external API
            logger.info(f"Using API mode with URL: {self.api_url}")
            items = self._crawl_via_api(max_pages)
        else:
            # HTML/Intelligent/LLM mode: Crawl web pages
            logger.info(f"Using HTML mode with base URL: {self.base_url}")
            items = self._crawl_via_html(max_pages)

        return items

    def _crawl_via_api(self, max_pages: int) -> List[Dict[str, Any]]:
        """
        Crawl using API calls.

        Args:
            max_pages: Maximum number of pages to fetch

        Returns:
            List of crawled items
        """
        items = []

        if not self.api_url:
            logger.error("API URL not configured")
            return items

        for page in range(self.page_start, self.page_start + max_pages):
            try:
                # Build request parameters
                params = dict(self.api_params)  # Copy template params
                params[self.page_param_name] = page

                # Make API request
                headers = {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                }
                headers.update(self.api_headers)

                logger.info(f"API Request: {self.api_method} {self.api_url} (page {page})")

                if self.api_method == 'GET':
                    response = requests.get(
                        self.api_url,
                        params=params,
                        headers=headers,
                        timeout=30
                    )
                else:
                    response = requests.post(
                        self.api_url,
                        json=params,
                        headers=headers,
                        timeout=30
                    )

                response.raise_for_status()
                data = response.json()

                # Parse API response
                page_items = self._parse_api_response(data)

                if not page_items:
                    logger.info(f"No more items on page {page}")
                    break

                # Create tender notices
                for item in page_items:
                    notice = self.create_tender_notice(item)
                    if notice:
                        items.append({
                            'notice_id': notice.notice_id,
                            'title': notice.title,
                            'source_url': notice.source_url
                        })

                logger.info(f"Page {page}: extracted {len(page_items)} items, created {len([i for i in page_items if i.get('_created')])} notices")

                # Delay between requests
                self.delay()

            except requests.RequestException as e:
                logger.error(f"API request failed on page {page}: {e}")
                break
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse API response on page {page}: {e}")
                break
            except Exception as e:
                logger.error(f"Unexpected error on page {page}: {e}")
                break

        return items

    def _parse_api_response(self, data: Dict) -> List[Dict[str, Any]]:
        """
        Parse API JSON response.

        Args:
            data: JSON response data

        Returns:
            List of parsed items
        """
        items = []

        try:
            # Navigate to data list using response path
            if self.api_response_path:
                # Support dot notation: data.middle.listAndBox
                list_data = data
                for key in self.api_response_path.split('.'):
                    if isinstance(list_data, dict) and key in list_data:
                        list_data = list_data[key]
                    else:
                        logger.warning(f"Could not find path: {self.api_response_path}")
                        return items
            else:
                # Try common paths
                for path in ['data', 'data.list', 'data.middle.listAndBox', 'results', 'items']:
                    list_data = data
                    for key in path.split('.'):
                        if isinstance(list_data, dict) and key in list_data:
                            list_data = list_data[key]
                        else:
                            list_data = None
                            break
                    if list_data:
                        break

            if not list_data:
                logger.warning("Could not find data list in API response")
                return items

            # Process each item
            for item_data in list_data:
                # Handle nested data structure
                if isinstance(item_data, dict) and 'data' in item_data:
                    item_data = item_data['data']

                item = self._extract_api_fields(item_data)
                if item and item.get('title'):
                    items.append(item)

        except Exception as e:
            logger.error(f"Error parsing API response: {e}")

        return items

    def _extract_api_fields(self, data: Dict) -> Optional[Dict[str, Any]]:
        """
        Extract fields from API item data.

        Args:
            data: Single item data from API

        Returns:
            Dictionary with extracted fields
        """
        if not isinstance(data, dict):
            return None

        def get_field(data: Dict, path: str, default=None):
            """Get field value using dot notation path"""
            if not path:
                return default
            value = data
            for key in path.split('.'):
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    return default
            return value if value is not None else default

        # Extract fields using configured paths
        title = get_field(data, self.api_field_title) or data.get('title', '')
        url = get_field(data, self.api_field_url) or data.get('url', '')
        date_str = get_field(data, self.api_field_date) or data.get('time', '')
        budget_str = get_field(data, self.api_field_budget) or data.get('budget', '')
        tenderer = get_field(data, self.api_field_tenderer) or data.get('tenderer', '')

        # Build URL if relative
        if url and not url.startswith('http'):
            url = urljoin(self.base_url, url)

        # Parse date
        publish_date = self.parse_date(str(date_str)[:19] if date_str else '')

        # Parse budget
        budget = None
        if budget_str:
            budget = self.parse_budget(str(budget_str))

        # Detect notice type from title
        notice_type = 'bidding'
        title_str = str(title) if title else ''
        if '中标' in title_str or '成交' in title_str or '结果' in title_str:
            notice_type = 'win'
        elif '变更' in title_str:
            notice_type = 'change'

        return {
            'title': str(title).strip() if title else '',
            'source_url': str(url).strip() if url else '',
            'publish_date': publish_date,
            'budget': budget,
            'tenderer': str(tenderer).strip() if tenderer else '',
            'notice_type': notice_type,
            'extraction_method': 'api',
            'extraction_confidence': 0.95,
        }

    def _crawl_via_html(self, max_pages: int) -> List[Dict[str, Any]]:
        """
        Crawl using HTML parsing.

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

        Uses configured selectors if available:
        - list_container_selector: Container holding all list items
        - list_item_selector: Each individual item in the list
        - list_link_selector: Link to detail page within each item

        Falls back to generic link extraction if not configured.

        Args:
            html: List page HTML content

        Returns:
            List of item dictionaries with 'url' and 'title' keys
        """
        items = []

        try:
            soup = BeautifulSoup(html, 'html.parser')

            # Use configured selectors if available
            if self.list_item_selector:
                # Configured mode: use specific selectors
                logger.debug(f"Using configured list selectors")

                # Find container if specified
                container = soup
                if self.list_container_selector:
                    containers = soup.select(self.list_container_selector)
                    if containers:
                        container = containers[0]

                # Find list items
                list_items = container.select(self.list_item_selector)
                logger.debug(f"Found {len(list_items)} list items")

                for item in list_items:
                    # Extract link
                    if self.list_link_selector:
                        links = item.select(self.list_link_selector)
                    else:
                        links = item.select('a[href]')

                    for link in links:
                        href = link.get('href', '')
                        text = link.get_text(strip=True)

                        if not href:
                            continue

                        # Skip non-http links
                        if href.startswith('javascript:') or href.startswith('#'):
                            continue

                        full_url = self.generate_detail_url(href)

                        if full_url.startswith(('http://', 'https://')):
                            items.append({
                                'url': full_url,
                                'title': text
                            })
                            break  # Take first valid link from each item
            else:
                # Generic mode: find all links
                logger.debug(f"Using generic link extraction")
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