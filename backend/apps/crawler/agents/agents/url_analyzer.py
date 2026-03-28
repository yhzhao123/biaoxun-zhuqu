"""
URL 分析智能体

分析爬取源配置，决定最佳爬取策略
"""
import logging
from typing import Dict, Any

from apps.crawler.models import CrawlSource
from apps.crawler.agents.schema import ExtractionStrategy

logger = logging.getLogger(__name__)


class URLAnalyzerAgent:
    """
    URL分析智能体

    分析招标网站结构，决定爬取策略
    """

    def __init__(self):
        pass

    async def analyze(self, source_config: CrawlSource) -> ExtractionStrategy:
        """
        分析爬取源，返回提取策略

        Args:
            source_config: 爬取源配置

        Returns:
            ExtractionStrategy 提取策略
        """
        logger.info(f"Analyzing source: {source_config.name}")

        # 根据 extraction_mode 决定策略
        if source_config.extraction_mode == 'api':
            return self._analyze_api_source(source_config)
        elif source_config.extraction_mode == 'dynamic':
            return self._analyze_dynamic_source(source_config)
        else:
            return self._analyze_static_source(source_config)

    def _analyze_api_source(self, source_config: CrawlSource) -> ExtractionStrategy:
        """分析API类型源"""
        logger.info(f"Using API strategy for {source_config.name}")

        strategy = ExtractionStrategy(
            site_type='api',
            max_pages=source_config.max_pages or 5,
            api_config={
                'url': source_config.api_url,
                'method': source_config.api_method or 'GET',
                'params': source_config.api_params or {},
                'headers': source_config.api_headers or {},
                'response_path': source_config.api_response_path,
            }
        )

        # 字段映射
        strategy.list_strategy = {
            'title_field': source_config.api_field_title or 'title',
            'url_field': source_config.api_field_url or 'url',
            'date_field': source_config.api_field_date or 'publish_date',
            'budget_field': source_config.api_field_budget or 'budget',
            'tenderer_field': source_config.api_field_tenderer or 'tenderer',
        }

        return strategy

    def _analyze_dynamic_source(self, source_config: CrawlSource) -> ExtractionStrategy:
        """分析动态渲染类型源"""
        logger.info(f"Using dynamic strategy for {source_config.name}")

        strategy = ExtractionStrategy(
            site_type='dynamic',
            max_pages=source_config.max_pages or 3,
        )

        # CSS选择器配置
        strategy.list_strategy = {
            'container': source_config.list_container_selector,
            'item': source_config.list_item_selector,
            'link': source_config.list_link_selector,
        }

        strategy.detail_strategy = {
            'title': source_config.selector_title,
            'content': source_config.selector_content,
            'tenderer': source_config.selector_tenderer,
            'publish_date': source_config.selector_publish_date,
            'budget': source_config.selector_budget,
        }

        # 动态渲染等待配置
        if source_config.wait_for_selector:
            strategy.detail_strategy['wait_for'] = source_config.wait_for_selector
            strategy.detail_strategy['wait_timeout'] = source_config.wait_timeout or 10

        return strategy

    def _analyze_static_source(self, source_config: CrawlSource) -> ExtractionStrategy:
        """分析静态页面类型源"""
        logger.info(f"Using static strategy for {source_config.name}")

        strategy = ExtractionStrategy(
            site_type='static',
            max_pages=source_config.max_pages or 3,
        )

        # 使用配置的选择器
        strategy.list_strategy = {
            'container': source_config.list_container_selector,
            'item': source_config.list_item_selector,
            'link': source_config.list_link_selector,
        }

        strategy.detail_strategy = {
            'title': source_config.selector_title,
            'content': source_config.selector_content,
            'tenderer': source_config.selector_tenderer,
            'publish_date': source_config.selector_publish_date,
            'budget': source_config.selector_budget,
        }

        return strategy
