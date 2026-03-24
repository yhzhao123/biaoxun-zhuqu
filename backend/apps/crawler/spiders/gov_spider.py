"""
Government procurement spider for ccgp.gov.cn
政府采购网爬虫
"""

import re
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from .base import BaseSpider


logger = logging.getLogger(__name__)


class GovSpider(BaseSpider):
    """
    中国政府采购网爬虫

    爬取政府采购公告，支持：
    - 招标公告
    - 中标公告
    - 采购变更公告
    """

    name = 'gov_spider'

    # 默认爬取URL
    DEFAULT_SOURCE_URL = 'http://www.ccgp.gov.cn/zcdt/'

    # 招标/中标关键词映射
    TENDER_KEYWORDS = ['招标', '采购', '询价', '竞争性谈判', '竞争性磋商', '单一来源']
    WIN_KEYWORDS = ['中标', '成交', '结果公告', '公示']

    def __init__(self, source_url: Optional[str] = None, **kwargs):
        """
        Initialize GovSpider

        Args:
            source_url: 爬取目标URL，默认使用 DEFAULT_SOURCE_URL
            **kwargs: 传递给 BaseSpider 的参数
        """
        super().__init__(**kwargs)
        self.source_url = source_url or self.DEFAULT_SOURCE_URL

    def crawl(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        执行爬取操作

        Args:
            limit: 限制爬取的条目数，None表示不限

        Returns:
            爬取的项目列表
        """
        logger.info(f"Starting crawl from: {self.source_url}")

        items = []
        page = 1

        while True:
            # 获取列表页
            list_url = self._build_list_url(page)
            try:
                response = self.fetch(list_url)
                announcements = self.parse_list_page(response)

                if not announcements:
                    logger.info("No more announcements found")
                    break

                logger.info(f"Found {len(announcements)} announcements on page {page}")

                # 遍历每个公告
                for announcement in announcements:
                    if limit and len(items) >= limit:
                        logger.info(f"Reached limit of {limit} items")
                        return items

                    try:
                        # 获取详情页
                        detail_url = announcement['url']
                        if not detail_url.startswith('http'):
                            detail_url = urljoin(self.source_url, detail_url)

                        detail_response = self.fetch(detail_url)
                        detail_data = self.parse_detail_page(detail_response)

                        # 合并列表页和详情页数据
                        item = {
                            **announcement,
                            **detail_data,
                            'source_url': detail_url,
                            'source_site': '政府采购网',
                        }

                        # 转换为 TenderNotice 格式
                        tender_item = self.transform_to_tender(item)
                        items.append(tender_item)

                    except Exception as e:
                        logger.error(f"Error fetching detail page {announcement.get('url')}: {e}")
                        continue

                page += 1

                # 简单的页数限制，避免无限循环
                if page > 10:
                    break

            except Exception as e:
                logger.error(f"Error fetching list page {page}: {e}")
                break

        logger.info(f"Crawl completed, total items: {len(items)}")
        return items

    def _build_list_url(self, page: int) -> str:
        """构建列表页URL"""
        if page == 1:
            return self.source_url
        # 根据实际网站的分页规则调整
        return f"{self.source_url}index_{page}.html"

    def parse_list_page(self, response) -> List[Dict[str, str]]:
        """
        解析列表页，提取公告链接

        Args:
            response: HTTP response object

        Returns:
            公告列表，每个包含 url, title, date
        """
        soup = BeautifulSoup(response.text, 'html.parser')
        announcements = []

        # 尝试多种可能的选择器
        # 中国政府采购网常见的列表结构
        selectors = [
            '.notice-list li',
            '.list-box li',
            '.ul-list li',
            '.con li',
            '.c_list_table tr',
            'ul li',
        ]

        items = []
        for selector in selectors:
            items = soup.select(selector)
            if items:
                break

        for item in items:
            try:
                # 尝试提取链接和标题
                link_elem = item.find('a')
                if not link_elem:
                    continue

                title = link_elem.get_text(strip=True)
                url = link_elem.get('href', '')

                if not title or not url:
                    continue

                # 提取日期
                date = ''
                date_elem = item.find(class_=re.compile('date|time'))
                if date_elem:
                    date = date_elem.get_text(strip=True)
                else:
                    # 尝试从文本中提取日期
                    text = item.get_text()
                    date_match = re.search(r'(\d{4}[-/年]\d{1,2}[-/月]\d{1,2})', text)
                    if date_match:
                        date = date_match.group(1).replace('年', '-').replace('月', '-').replace('/', '-')

                announcements.append({
                    'url': url,
                    'title': title,
                    'date': date,
                })

            except Exception as e:
                logger.warning(f"Error parsing list item: {e}")
                continue

        return announcements

    def parse_detail_page(self, response) -> Dict[str, Any]:
        """
        解析详情页，提取完整公告信息

        Args:
            response: HTTP response object

        Returns:
            提取的公告详情数据
        """
        soup = BeautifulSoup(response.text, 'html.parser')
        content_text = soup.get_text()

        data = {
            'title': self._extract_title(soup),
            'publish_date': self._extract_date(content_text, 'publish'),
            'bid_number': self._extract_bid_number(content_text),
            'bidder': self._extract_bidder(content_text),
            'agency': self._extract_agency(content_text),
            'budget_amount': self._extract_amount(content_text),
            'open_date': self._extract_date(content_text, 'open'),
            'content': self._extract_content(soup),
        }

        return data

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """提取标题"""
        selectors = ['h1.title', 'h1', '.title', '.notice-title', '#title']
        for selector in selectors:
            elem = soup.select_one(selector)
            if elem:
                return elem.get_text(strip=True)
        return ''

    def _extract_date(self, text: str, date_type: str = 'publish') -> Optional[str]:
        """
        提取日期

        Args:
            text: 文本内容
            date_type: 'publish' 或 'open' (开标日期)
        """
        patterns = {
            'publish': [
                r'发布时间[:：]\s*(\d{4}[-/年]\d{1,2}[-/月]\d{1,2})',
                r'(\d{4}[-/年]\d{1,2}[-/月]\d{1,2})\s*发布',
                r'(\d{4}年\d{1,2}月\d{1,2}日)',
                r'(\d{4}/\d{1,2}/\d{1,2})',
            ],
            'open': [
                r'开标时间[:：]\s*(\d{4}[-/年]\d{1,2}[-/月]\d{1,2})',
                r'投标截止.*?时间[:：]\s*(\d{4}[-/年]\d{1,2}[-/月]\d{1,2})',
                r'(\d{4}[-/年]\d{1,2}[-/月]\d{1,2})\s*开标',
            ]
        }

        for pattern in patterns.get(date_type, patterns['publish']):
            match = re.search(pattern, text)
            if match:
                date_str = match.group(1)
                # 标准化日期格式
                date_str = date_str.replace('年', '-').replace('月', '-').replace('/', '-')
                # 移除末尾的日
                date_str = date_str.rstrip('日')
                # 确保月份和日期是两位数
                parts = date_str.split('-')
                if len(parts) == 3:
                    return f"{parts[0]}-{parts[1].zfill(2)}-{parts[2].zfill(2)}"
                return date_str

        return None

    def _extract_bid_number(self, text: str) -> Optional[str]:
        """提取招标编号"""
        patterns = [
            r'招标编号[:：]\s*([A-Za-z0-9\-]+)',
            r'项目编号[:：]\s*([A-Za-z0-9\-]+)',
            r'采购编号[:：]\s*([A-Za-z0-9\-]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()

        return None

    def _extract_bidder(self, text: str) -> Optional[str]:
        """提取招标人/采购人"""
        patterns = [
            r'招标人[:：]\s*([^\n]+)',
            r'采购人[:：]\s*([^\n]+)',
            r'采购单位[:：]\s*([^\n]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()

        return None

    def _extract_agency(self, text: str) -> Optional[str]:
        """提取招标代理机构"""
        patterns = [
            r'招标代理.*?[:：]\s*([^\n]+)',
            r'采购代理.*?[:：]\s*([^\n]+)',
            r'代理机构[:：]\s*([^\n]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()

        return None

    def _extract_amount(self, text: str) -> Optional[str]:
        """
        提取金额

        支持格式：
        - ¥100,000.00
        - 100万元
        - 预算金额：500000元
        """
        patterns = [
            r'预算金额[:：]\s*[¥￥]?\s*([\d,\.]+)\s*元?',
            r'采购预算[:：]\s*[¥￥]?\s*([\d,\.]+)\s*元?',
            r'项目金额[:：]\s*[¥￥]?\s*([\d,\.]+)',
            r'[¥￥]\s*([\d,\.]+)\s*[万元]?',
            r'(\d+)\s*万元',
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                amount = match.group(1).replace(',', '')
                # 处理"万元"单位
                if '万元' in text[match.start():match.end()+10]:
                    try:
                        amount = str(int(float(amount) * 10000))
                    except ValueError:
                        pass
                return amount

        return None

    def _extract_content(self, soup: BeautifulSoup) -> str:
        """提取正文内容"""
        selectors = [
            '.notice-content',
            '.content',
            '.detail-content',
            '.article-content',
            '.vF_detail_content',
        ]

        for selector in selectors:
            elem = soup.select_one(selector)
            if elem:
                return elem.get_text(strip=True, separator='\n')

        # 如果找不到特定内容区，返回body文本
        body = soup.find('body')
        if body:
            return body.get_text(strip=True, separator='\n')[:2000]

        return ''

    def _extract_bid_type(self, title: str) -> str:
        """
        根据标题判断公告类型

        Returns:
            'tender' - 招标公告
            'win' - 中标公告
        """
        title = title.lower()

        # 检查中标关键词
        for keyword in self.WIN_KEYWORDS:
            if keyword in title:
                return 'win'

        # 默认返回招标
        return 'tender'

    def transform_to_tender(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        将爬取的数据转换为 TenderNotice 格式

        Args:
            item: 爬取的数据

        Returns:
            TenderNotice 格式的数据
        """
        notice_type = self._extract_bid_type(item.get('title', ''))

        return {
            'title': item.get('title', ''),
            'notice_type': notice_type,
            'bid_number': item.get('bid_number'),
            'publish_date': item.get('publish_date'),
            'open_date': item.get('open_date'),
            'bidder_name': item.get('bidder'),
            'agency_name': item.get('agency'),
            'budget_amount': item.get('budget_amount'),
            'content': item.get('content'),
            'source_url': item.get('source_url'),
            'source_site': item.get('source_site', '政府采购网'),
            'status': 'active',
        }
