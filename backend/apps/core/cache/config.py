"""
Django缓存配置模块

定义缓存TTL和基本配置
"""

# 招标列表缓存 TTL: 5分钟
TENDER_LIST_TTL = 300

# 招标详情缓存 TTL: 10分钟
TENDER_DETAIL_TTL = 600

# 统计数据缓存 TTL: 30分钟
STATS_TTL = 1800

# 搜索结果缓存 TTL: 2分钟
SEARCH_TTL = 120

# 地区分布缓存 TTL: 30分钟
REGION_DISTRIBUTION_TTL = 1800

# 行业分布缓存 TTL: 30分钟
INDUSTRY_DISTRIBUTION_TTL = 1800

# 默认缓存TTL
DEFAULT_TTL = 300

# 缓存键前缀
CACHE_KEY_PREFIX = 'biaoxun'

# 缓存版本
CACHE_VERSION = 'v1'