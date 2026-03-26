"""
JilinSpider - 吉林省公共资源交易中心爬虫

针对动态加载网站，直接调用API获取数据

网站结构分析:
- 主站: http://www.ggzyzx.jl.gov.cn/
- 数据API: https://haiyun.jl.gov.cn/irs/front/search
- 数据类型: 政府采购、工程建设、土地矿产、产权交易

API参数:
- channel_id: 栏目ID (政府采购、工程建设等)
- pageNo: 页码
- pageSize: 每页数量
"""

import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from decimal import Decimal

import requests

from apps.crawler.spiders.base import BaseSpider
from apps.tenders.models import TenderNotice

logger = logging.getLogger(__name__)


class JilinSpider(BaseSpider):
    """
    吉林省公共资源交易中心爬虫

    特点:
    - 直接调用API获取数据，无需解析HTML
    - 支持多种交易类型
    - 自动分页
    """

    name = 'jilin_spider'

    # API配置
    API_URL = "https://haiyun.jl.gov.cn/irs/front/search"

    # 栏目ID映射
    CHANNEL_IDS = {
        '政府采购': 'zfcg',  # 需要实际获取正确的ID
        '工程建设': 'gcjs',
        '土地矿产': 'tdkc',
        '产权交易': 'cqjy',
    }

    # 招标类型映射
    NOTICE_TYPE_MAP = {
        '招标公告': 'bidding',
        '中标公告': 'win',
        '成交公告': 'win',
        '结果公示': 'win',
        '变更公告': 'change',
        '答疑公告': 'qa',
    }

    def __init__(self, **kwargs):
        """初始化"""
        super().__init__(min_delay=1, max_delay=2, **kwargs)

        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Origin': 'http://www.ggzyzx.jl.gov.cn',
            'Referer': 'http://www.ggzyzx.jl.gov.cn/jyxx/zfcg/',
        })

    def crawl(self, channel: str = '政府采购', max_pages: int = 5) -> List[Dict[str, Any]]:
        """
        执行爬取

        Args:
            channel: 栏目名称 (政府采购、工程建设、土地矿产、产权交易)
            max_pages: 最大爬取页数

        Returns:
            爬取结果列表
        """
        results = []

        for page in range(1, max_pages + 1):
            try:
                # 构建请求参数
                params = self._build_params(channel, page)

                # 发送请求
                response = self.session.post(
                    self.API_URL,
                    json=params,
                    timeout=30
                )
                response.raise_for_status()

                data = response.json()

                # 解析数据
                items = self._parse_response(data)

                if not items:
                    logger.info(f"No more items on page {page}")
                    break

                # 创建招标公告
                for item in items:
                    notice = self._create_notice(item)
                    if notice:
                        results.append({
                            'notice_id': notice.notice_id,
                            'title': notice.title,
                            'source_url': notice.source_url
                        })

                logger.info(f"Page {page}: crawled {len(items)} items")

                # 延迟
                self.delay()

            except Exception as e:
                logger.error(f"Error crawling page {page}: {e}")
                break

        return results

    def _build_params(self, channel: str, page: int, page_size: int = 20) -> Dict:
        """
        构建API请求参数

        注意: 这里的参数可能需要根据实际API调整
        """
        return {
            "channel_id": self.CHANNEL_IDS.get(channel, 'zfcg'),
            "pageNo": page,
            "pageSize": page_size,
            "word": None,
            "startDateTime": None,
            "endDateTime": None,
            "isSearchForced": 0,
            "customFilter": {
                "operator": "and",
                "properties": []
            }
        }

    def _parse_response(self, data: Dict) -> List[Dict]:
        """解析API响应"""
        items = []

        try:
            # 根据实际API结构解析
            # 这里的路径可能需要调整
            list_data = data.get('data', {}).get('middle', {}).get('listAndBox', [])

            for item in list_data:
                record = item.get('data', {})

                parsed = {
                    'title': record.get('title', ''),
                    'publish_date': self._parse_date(record.get('time', '')),
                    'source_url': record.get('url', ''),
                    'notice_type': self._detect_notice_type(record.get('title', '')),
                    'channel': record.get('channel', ''),
                }

                items.append(parsed)

        except Exception as e:
            logger.error(f"Error parsing response: {e}")

        return items

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """解析日期"""
        if not date_str:
            return None

        try:
            # 格式: 2024-01-15 或 2024-01-15 10:30:00
            return datetime.strptime(date_str[:10], '%Y-%m-%d')
        except ValueError:
            return None

    def _detect_notice_type(self, title: str) -> str:
        """根据标题判断公告类型"""
        title_lower = title.lower()

        for keyword, notice_type in self.NOTICE_TYPE_MAP.items():
            if keyword in title:
                return notice_type

        return 'bidding'

    def _create_notice(self, data: Dict) -> Optional[TenderNotice]:
        """创建招标公告"""
        try:
            title = data.get('title', '').strip()
            source_url = data.get('source_url', '').strip()

            if not title:
                return None

            # 检查重复
            existing = TenderNotice.objects.filter(
                title=title,
                source_url=source_url
            ).first()

            if existing:
                return existing

            # 生成ID
            from django.utils.text import slugify
            import uuid
            notice_id = f"{slugify(title)[:30]}-{uuid.uuid4().hex[:8]}"

            notice = TenderNotice.objects.create(
                notice_id=notice_id,
                title=title,
                publish_date=data.get('publish_date'),
                source_url=source_url,
                source_site='吉林省公共资源交易中心',
                notice_type=data.get('notice_type', 'bidding'),
                status='active'
            )

            logger.info(f"Created TenderNotice: {notice.notice_id}")
            return notice

        except Exception as e:
            logger.error(f"Error creating notice: {e}")
            return None


# 用于直接运行测试
if __name__ == '__main__':
    spider = JilinSpider()
    results = spider.crawl(channel='政府采购', max_pages=2)
    print(f"Crawled {len(results)} items")