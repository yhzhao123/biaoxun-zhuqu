"""
Crawler spiders module
"""
from .base import BaseSpider
from .gov_spider import GovSpider
from .dynamic import DynamicSpider

__all__ = ['BaseSpider', 'GovSpider', 'DynamicSpider']