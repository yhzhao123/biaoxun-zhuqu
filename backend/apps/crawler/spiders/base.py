"""
Base spider class for all crawlers
"""

import random
import time
import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, List, Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


logger = logging.getLogger(__name__)


# User-Agent轮换池
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0',
]


class BaseSpider(ABC):
    """
    爬虫基类，提供反爬策略和通用方法

    Features:
    - Random delay between requests
    - User-Agent rotation
    - Retry mechanism
    - Proxy support (optional)
    """

    name: str = 'base_spider'

    def __init__(
        self,
        min_delay: float = 1.0,
        max_delay: float = 3.0,
        timeout: int = 30,
        max_retries: int = 3,
        proxies: Optional[List[str]] = None
    ):
        """
        Initialize spider

        Args:
            min_delay: Minimum delay between requests (seconds)
            max_delay: Maximum delay between requests (seconds)
            timeout: Request timeout (seconds)
            max_retries: Maximum retry attempts
            proxies: List of proxy URLs
        """
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.timeout = timeout
        self.max_retries = max_retries
        self.proxies = proxies or []
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        """Create a requests session with retry strategy"""
        session = requests.Session()

        # Configure retry strategy
        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    def _get_random_headers(self) -> Dict[str, str]:
        """Generate random headers including User-Agent"""
        return {
            'User-Agent': random.choice(USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }

    def _get_proxy(self) -> Optional[Dict[str, str]]:
        """Get a random proxy from the pool"""
        if self.proxies:
            proxy = random.choice(self.proxies)
            return {
                'http': proxy,
                'https': proxy,
            }
        return None

    def _random_delay(self):
        """Apply random delay between requests"""
        delay = random.uniform(self.min_delay, self.max_delay)
        logger.debug(f"Sleeping for {delay:.2f} seconds")
        time.sleep(delay)

    def fetch(self, url: str, **kwargs) -> requests.Response:
        """
        Fetch a URL with anti-crawling strategies

        Args:
            url: URL to fetch
            **kwargs: Additional arguments to pass to requests

        Returns:
            Response object
        """
        self._random_delay()

        headers = self._get_random_headers()
        if 'headers' in kwargs:
            headers.update(kwargs.pop('headers'))

        proxies = self._get_proxy()
        if proxies and 'proxies' not in kwargs:
            kwargs['proxies'] = proxies

        kwargs.setdefault('timeout', self.timeout)
        kwargs.setdefault('headers', headers)

        logger.info(f"Fetching: {url}")
        response = self.session.get(url, **kwargs)
        response.raise_for_status()

        return response

    @abstractmethod
    def crawl(self) -> List[Dict[str, Any]]:
        """
        Execute the crawl operation

        Returns:
            List of crawled items
        """
        pass

    def parse(self, response: requests.Response) -> Any:
        """
        Parse the response (can be overridden by subclasses)

        Args:
            response: Response object

        Returns:
            Parsed data
        """
        # Default implementation just returns the response text
        # Subclasses should override this to provide actual parsing
        return response.text

    def save_item(self, item: Dict[str, Any]) -> bool:
        """
        Save a crawled item (to be implemented with database)

        Args:
            item: Item to save

        Returns:
            True if saved successfully
        """
        # This method should be overridden to save to database
        logger.info(f"Saving item: {item.get('title', 'No title')}")
        return True