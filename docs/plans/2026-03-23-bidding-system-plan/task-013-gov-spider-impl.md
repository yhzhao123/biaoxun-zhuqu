# Task 013: 政府采购网爬虫实现

## 任务信息

- **任务ID**: 013
- **任务名称**: 政府采购网爬虫实现
- **任务类型**: impl
- **依赖任务**: 012 (政府采购网爬虫测试)

## BDD Scenario

```gherkin
Scenario: 成功爬取政府采购网信息
  Given 爬虫任务"政府采购网-每日更新"已配置
  And 目标URL为"http://www.ccgp.gov.cn/"
  When 爬虫在每日凌晨2:00启动
  Then 应在4小时内完成爬取
  And 成功提取的招标信息数量应大于0
  And 所有提取的数据应包含title、notice_id、tenderer字段
```

## 实现目标

实现中国政府采购网爬虫，支持列表页和详情页解析，处理反爬机制，数据标准化。

## 创建/修改的文件

- `apps/crawler/spiders/gov_spider.py` - 政府网爬虫实现
- `apps/crawler/parsers/gov_parser.py` - 页面解析器
- `apps/crawler/utils/data_normalizer.py` - 数据标准化
- `apps/crawler/exceptions.py` - 自定义异常
- `apps/crawler/middlewares.py` - 下载中间件

## 实施步骤

### 1. 创建政府网爬虫

```python
# apps/crawler/spiders/gov_spider.py
import scrapy
from scrapy.http import Request
from urllib.parse import urljoin, urlparse
import re
from datetime import datetime
import logging

from apps.crawler.base import SpiderConfig
from apps.crawler.spiders import register_spider
from apps.crawler.parsers.gov_parser import GovListParser, GovDetailParser
from apps.crawler.utils.data_normalizer import DataNormalizer
from apps.tenders.models import TenderNotice

logger = logging.getLogger(__name__)


@register_spider
class GovSpider(scrapy.Spider):
    """中国政府采购网爬虫"""
    name = 'gov_spider'
    allowed_domains = ['ccgp.gov.cn', 'www.ccgp.gov.cn']

    custom_settings = {
        'ROBOTSTXT_OBEY': True,
        'DOWNLOAD_DELAY': 2,
        'RANDOMIZE_DOWNLOAD_DELAY': 1,
        'CONCURRENT_REQUESTS': 2,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 2,
        'RETRY_TIMES': 5,
        'RETRY_HTTP_CODES': [500, 502, 503, 504, 408, 429],
        'COOKIES_ENABLED': False,
        'DEFAULT_REQUEST_HEADERS': {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9',
        },
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.start_urls = kwargs.get('start_urls', [
            'http://www.ccgp.gov.cn/cggg/dfgg/',
        ])
        self.max_pages = kwargs.get('max_pages', 100)
        self.pages_crawled = 0
        self.list_parser = GovListParser()
        self.detail_parser = GovDetailParser()
        self.normalizer = DataNormalizer()

    def start_requests(self):
        for url in self.start_urls:
            yield Request(url, callback=self.parse_list, meta={'page': 1})

    def parse_list(self, response):
        """解析列表页"""
        self.pages_crawled += 1
        logger.info(f"Parsing list page {response.meta.get('page', 1)}: {response.url}")

        # 解析列表项
        items = self.list_parser.parse(response)

        for item in items:
            detail_url = item.get('detail_url')
            if detail_url:
                yield Request(
                    urljoin(response.url, detail_url),
                    callback=self.parse_detail,
                    meta={'list_item': item},
                    errback=self.handle_error
                )

        # 下一页
        if self.pages_crawled < self.max_pages:
            next_page = self.list_parser.get_next_page(response)
            if next_page:
                yield Request(
                    urljoin(response.url, next_page),
                    callback=self.parse_list,
                    meta={'page': response.meta.get('page', 1) + 1}
                )

    def parse_detail(self, response):
        """解析详情页"""
        logger.info(f"Parsing detail page: {response.url}")

        list_item = response.meta.get('list_item', {})
        detail_data = self.detail_parser.parse(response)

        # 合并列表和详情数据
        data = {**list_item, **detail_data}
        data['source_url'] = response.url
        data['source_site'] = 'ccgp.gov.cn'

        # 标准化数据
        normalized = self.normalizer.normalize(data)

        # 保存到数据库
        try:
            self.save_tender(normalized)
            yield normalized
        except Exception as e:
            logger.error(f"Failed to save tender: {e}")
            yield {'error': str(e), 'data': normalized}

    def save_tender(self, data):
        """保存招标信息"""
        notice_id = data.get('notice_id')
        if not notice_id:
            logger.warning("Missing notice_id, skipping save")
            return

        TenderNotice.objects.update_or_create(
            notice_id=notice_id,
            defaults={
                'title': data.get('title', ''),
                'description': data.get('description', ''),
                'tenderer': data.get('tenderer', ''),
                'budget': data.get('budget'),
                'currency': data.get('currency', 'CNY'),
                'publish_date': data.get('publish_date'),
                'deadline_date': data.get('deadline_date'),
                'region': data.get('region', ''),
                'industry': data.get('industry', ''),
                'source_url': data.get('source_url', ''),
                'source_site': data.get('source_site', ''),
                'status': 'pending'
            }
        )
        logger.info(f"Saved tender: {notice_id}")

    def handle_error(self, failure):
        """处理错误"""
        logger.error(f"Request failed: {failure}")
        return {
            'error': str(failure),
            'url': failure.request.url if hasattr(failure, 'request') else None
        }
```

### 2. 创建页面解析器

```python
# apps/crawler/parsers/gov_parser.py
import re
from datetime import datetime
from scrapy.selector import Selector
import logging

logger = logging.getLogger(__name__)


class GovListParser:
    """政府采购网列表页解析器"""

    def parse(self, response):
        """解析列表页"""
        selector = Selector(response)
        items = []

        # 列表项选择器
        rows = selector.css('.vT-srch-result-list .vT-srch-result-list-bid') or \
               selector.css('.c_list_item') or \
               selector.css('ul li')

        for row in rows:
            item = self._parse_row(row)
            if item:
                items.append(item)

        return items

    def _parse_row(self, row):
        """解析单行数据"""
        try:
            title = self._extract_text(row.css('a::text'))
            detail_url = row.css('a::attr(href)').get('')
            publish_date = self._extract_date(row.css('.c_list_date::text').get(''))
            region = row.css('.c_list_region::text').get('')

            if not title:
                return None

            return {
                'title': title.strip(),
                'detail_url': detail_url.strip() if detail_url else '',
                'publish_date': publish_date,
                'region': region.strip() if region else '',
            }
        except Exception as e:
            logger.error(f"Failed to parse row: {e}")
            return None

    def get_next_page(self, response):
        """获取下一页链接"""
        selector = Selector(response)

        # 尝试多种分页选择器
        next_link = selector.css('.page .next::attr(href)').get('') or \
                    selector.css('.p_next::attr(href)').get('') or \
                    selector.css('a:contains("下一页")::attr(href)').get('')

        return next_link if next_link else None

    def _extract_text(self, selector):
        """提取文本"""
        texts = selector.getall()
        return ' '.join(t.strip() for t in texts if t.strip())

    def _extract_date(self, text):
        """提取日期"""
        if not text:
            return None
        patterns = [
            r'(\d{4})[年/-](\d{1,2})[月/-](\d{1,2})',
            r'(\d{4})(\d{2})(\d{2})',
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    return datetime(
                        int(match.group(1)),
                        int(match.group(2)),
                        int(match.group(3))
                    ).date()
                except ValueError:
                    pass
        return None


class GovDetailParser:
    """政府采购网详情页解析器"""

    def parse(self, response):
        """解析详情页"""
        selector = Selector(response)

        data = {
            'notice_id': self._extract_notice_id(response),
            'title': self._extract_title(selector),
            'description': self._extract_description(selector),
            'tenderer': self._extract_tenderer(selector),
            'budget': self._extract_budget(selector),
            'publish_date': self._extract_publish_date(selector),
            'deadline_date': self._extract_deadline(selector),
            'region': self._extract_region(selector),
            'industry': self._extract_industry(selector),
            'contact_info': self._extract_contact(selector),
        }

        return {k: v for k, v in data.items() if v is not None}

    def _extract_notice_id(self, response):
        """提取公告编号"""
        # 从URL中提取
        import re
        match = re.search(r'/(\d{4,})/', response.url)
        if match:
            return match.group(1)

        # 从页面内容提取
        selector = Selector(response)
        notice_id = selector.css('.notice_id::text').get('') or \
                   selector.re_first(r'公告编号[:：]\s*(\w+)')
        return notice_id.strip() if notice_id else None

    def _extract_title(self, selector):
        """提取标题"""
        title = selector.css('.vF_detail_header h2::text').get('') or \
                selector.css('.c_title::text').get('') or \
                selector.css('h1::text').get('')
        return title.strip() if title else None

    def _extract_description(self, selector):
        """提取描述/正文"""
        content = selector.css('.vF_detail_content').get('') or \
                 selector.css('.c_content').get('') or \
                 selector.css('.content').get('')
        # 清理HTML标签
        import re
        text = re.sub(r'<[^>]+>', '', content)
        return text.strip() if text else None

    def _extract_tenderer(self, selector):
        """提取招标人"""
        patterns = [
            r'采购人[:：]\s*([^\n]+)',
            r'招标人[:：]\s*([^\n]+)',
            r'采购单位[:：]\s*([^\n]+)',
        ]
        text = selector.get()
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()
        return None

    def _extract_budget(self, selector):
        """提取预算金额"""
        patterns = [
            r'预算金额[:：]\s*([^\n]+)',
            r'采购预算[:：]\s*([^\n]+)',
            r'最高限价[:：]\s*([^\n]+)',
        ]
        text = selector.get()
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return self._parse_amount(match.group(1))
        return None

    def _extract_publish_date(self, selector):
        """提取发布日期"""
        text = selector.css('.vF_detail_info::text').get('') or \
               selector.css('.c_date::text').get('')
        if text:
            match = re.search(r'(\d{4})[年/-](\d{1,2})[月/-](\d{1,2})', text)
            if match:
                try:
                    return datetime(
                        int(match.group(1)),
                        int(match.group(2)),
                        int(match.group(3))
                    ).date()
                except ValueError:
                    pass
        return None

    def _extract_deadline(self, selector):
        """提取截止日期"""
        patterns = [
            r'投标截止.*?([\d年月日\-]+)',
            r'截止时间[:：]\s*([\d年月日\-]+)',
        ]
        text = selector.get()
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                # 解析日期
                date_str = match.group(1)
                return self._parse_date(date_str)
        return None

    def _extract_region(self, selector):
        """提取地区"""
        region = selector.css('.region::text').get('')
        return region.strip() if region else None

    def _extract_industry(self, selector):
        """提取行业"""
        industry = selector.css('.industry::text').get('')
        return industry.strip() if industry else None

    def _extract_contact(self, selector):
        """提取联系方式"""
        contact = {}
        text = selector.get()

        # 提取电话
        phone_match = re.search(r'联系电话[:：]\s*([\d\-]+)', text)
        if phone_match:
            contact['phone'] = phone_match.group(1)

        # 提取邮箱
        email_match = re.search(r'[\w.-]+@[\w.-]+\.\w+', text)
        if email_match:
            contact['email'] = email_match.group(0)

        return contact if contact else None

    def _parse_amount(self, text):
        """解析金额"""
        import re
        # 提取数字
        numbers = re.findall(r'[\d,\.]+', text.replace(',', ''))
        if numbers:
            try:
                return float(numbers[0])
            except ValueError:
                pass
        return None

    def _parse_date(self, text):
        """解析日期"""
        import re
        match = re.search(r'(\d{4})[年/-]?(\d{1,2})[月/-]?(\d{1,2})', text)
        if match:
            try:
                return datetime(
                    int(match.group(1)),
                    int(match.group(2)),
                    int(match.group(3))
                ).date()
            except ValueError:
                pass
        return None
```

### 3. 创建数据标准化工具

```python
# apps/crawler/utils/data_normalizer.py
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation
import logging

logger = logging.getLogger(__name__)


class DataNormalizer:
    """数据标准化工具"""

    def normalize(self, data):
        """标准化数据"""
        normalized = {}

        # 标题：去除多余空格
        if 'title' in data:
            normalized['title'] = self._normalize_title(data['title'])

        # 公告编号：去除空格，统一格式
        if 'notice_id' in data:
            normalized['notice_id'] = self._normalize_notice_id(data['notice_id'])

        # 招标人：去除多余信息
        if 'tenderer' in data:
            normalized['tenderer'] = self._normalize_tenderer(data['tenderer'])

        # 预算：统一为Decimal
        if 'budget' in data:
            normalized['budget'] = self._normalize_budget(data['budget'])

        # 日期：统一为date对象
        if 'publish_date' in data:
            normalized['publish_date'] = self._normalize_date(data['publish_date'])

        if 'deadline_date' in data:
            normalized['deadline_date'] = self._normalize_date(data['deadline_date'])

        # 地区：标准化
        if 'region' in data:
            normalized['region'] = self._normalize_region(data['region'])

        # 行业：标准化
        if 'industry' in data:
            normalized['industry'] = self._normalize_industry(data['industry'])

        # 保留其他字段
        for key in ['source_url', 'source_site', 'description', 'contact_info']:
            if key in data:
                normalized[key] = data[key]

        return normalized

    def _normalize_title(self, title):
        """标准化标题"""
        if not title:
            return ''
        # 去除多余空格
        title = ' '.join(title.split())
        # 去除首尾特殊字符
        title = title.strip(' \t\n\r\ufeff')
        return title

    def _normalize_notice_id(self, notice_id):
        """标准化公告编号"""
        if not notice_id:
            return None
        return str(notice_id).strip().upper()

    def _normalize_tenderer(self, tenderer):
        """标准化招标人"""
        if not tenderer:
            return ''
        # 去除多余空格
        tenderer = ' '.join(tenderer.split())
        # 去除常见前缀
        prefixes = ['采购人：', '招标人：', '采购单位：']
        for prefix in prefixes:
            if tenderer.startswith(prefix):
                tenderer = tenderer[len(prefix):]
        return tenderer.strip()

    def _normalize_budget(self, budget):
        """标准化预算金额"""
        if budget is None:
            return None

        if isinstance(budget, (int, float, Decimal)):
            return Decimal(str(budget))

        if isinstance(budget, str):
            # 提取数字
            budget = budget.replace(',', '').replace('，', '')
            # 去除货币符号
            budget = re.sub(r'[¥￥$€£]', '', budget)
            # 提取第一个数字
            match = re.search(r'[\d\.]+', budget)
            if match:
                try:
                    # 处理"万"、"亿"
                    amount_str = match.group(0)
                    amount = Decimal(amount_str)
                    if '万' in budget:
                        amount *= 10000
                    elif '亿' in budget:
                        amount *= 100000000
                    return amount
                except (InvalidOperation, ValueError):
                    pass

        return None

    def _normalize_date(self, date):
        """标准化日期"""
        if date is None:
            return None

        if isinstance(date, datetime):
            return date.date() if hasattr(date, 'date') else date

        if isinstance(date, str):
            patterns = [
                (r'(\d{4})-(\d{1,2})-(\d{1,2})', '%Y-%m-%d'),
                (r'(\d{4})/(\d{1,2})/(\d{1,2})', '%Y/%m/%d'),
                (r'(\d{4})年(\d{1,2})月(\d{1,2})日', '%Y年%m月%d日'),
            ]
            for pattern, fmt in patterns:
                match = re.match(pattern, date)
                if match:
                    try:
                        return datetime.strptime(date, fmt).date()
                    except ValueError:
                        pass

        return None

    def _normalize_region(self, region):
        """标准化地区"""
        if not region:
            return ''
        region = region.strip()
        # 去除"省"、"市"、"区"等后缀用于匹配
        return region

    def _normalize_industry(self, industry):
        """标准化行业"""
        if not industry:
            return ''
        return industry.strip()
```

### 4. 创建自定义异常

```python
# apps/crawler/exceptions.py


class CrawlerException(Exception):
    """爬虫基础异常"""
    pass


class SpiderConfigError(CrawlerException):
    """爬虫配置错误"""
    pass


class ParseError(CrawlerException):
    """解析错误"""
    pass


class RateLimitError(CrawlerException):
    """请求频率限制"""
    pass


class AntiCrawlDetected(CrawlerException):
    """检测到反爬"""
    pass


class DataValidationError(CrawlerException):
    """数据验证错误"""
    pass
```

### 5. 创建下载中间件

```python
# apps/crawler/middlewares.py
import random
import time
from scrapy.downloadermiddlewares.retry import RetryMiddleware
from scrapy.exceptions import IgnoreRequest
import logging

from .exceptions import RateLimitError, AntiCrawlDetected

logger = logging.getLogger(__name__)


class RotateUserAgentMiddleware:
    """轮换User-Agent"""

    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
    ]

    def process_request(self, request, spider):
        request.headers['User-Agent'] = random.choice(self.USER_AGENTS)
        return None


class ProxyMiddleware:
    """代理中间件"""

    def __init__(self, proxies=None):
        self.proxies = proxies or []

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            proxies=crawler.settings.getlist('PROXIES')
        )

    def process_request(self, request, spider):
        if self.proxies:
            proxy = random.choice(self.proxies)
            request.meta['proxy'] = proxy
        return None


class RetryOnRateLimitMiddleware(RetryMiddleware):
    """频率限制重试中间件"""

    def process_response(self, request, response, spider):
        if response.status == 429:
            logger.warning(f"Rate limit hit for {request.url}")
            reason = f"rate_limit_{response.status}"
            return self._retry(request, reason, spider) or response

        # 检测反爬页面
        if self._is_anti_crawl_page(response):
            logger.warning(f"Anti-crawl detected for {request.url}")
            raise AntiCrawlDetected(f"Anti-crawl detected on {request.url}")

        return super().process_response(request, response, spider)

    def _is_anti_crawl_page(self, response):
        """检测是否为反爬页面"""
        anti_crawl_keywords = [
            '访问过于频繁',
            '验证码',
            'captcha',
            '请稍后重试',
        ]
        text = response.text.lower()
        return any(keyword in text for keyword in anti_crawl_keywords)


class DelayMiddleware:
    """动态延迟中间件"""

    def __init__(self, crawler):
        self.stats = crawler.stats
        self.base_delay = crawler.settings.getfloat('DOWNLOAD_DELAY', 1)

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    def process_request(self, request, spider):
        # 根据成功率调整延迟
        if self.stats:
            success = self.stats.get_value('response_received_count', 0)
            errors = self.stats.get_value('retry/max_reached', 0)
            if errors > success * 0.1:  # 错误率超过10%
                delay = self.base_delay * 2
                logger.info(f"Increasing delay to {delay}s due to high error rate")
                time.sleep(delay)
        return None
```

## 验证步骤

```bash
# 运行政府网爬虫测试
pytest apps/crawler/tests/test_gov_spider.py -v

# 测试爬虫配置
python -c "from apps.crawler.spiders.gov_spider import GovSpider; print(GovSpider.name)"

# 验证数据标准化
python -c "
from apps.crawler.utils.data_normalizer import DataNormalizer
n = DataNormalizer()
result = n.normalize({'budget': '¥1,000,000.00'})
print(result)
"
```

**预期**: 所有测试通过(GREEN状态)

## 提交信息

```
feat: implement government procurement spider

- Add GovSpider for ccgp.gov.cn with Scrapy integration
- Implement GovListParser for list page extraction
- Implement GovDetailParser for detail page extraction
- Add DataNormalizer for standardizing extracted data
- Create custom exceptions (RateLimitError, AntiCrawlDetected, etc.)
- Add middlewares for UA rotation, proxy support, rate limiting
- Support pagination, anti-crawl detection, and error handling
- Save crawled data to TenderNotice model
- All tests passing (GREEN state)
```
