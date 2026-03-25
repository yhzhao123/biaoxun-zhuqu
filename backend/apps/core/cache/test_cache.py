"""
Django缓存策略配置 - TDD测试套件

测试覆盖:
- 缓存键名生成器
- 缓存装饰器
- 缓存管理器
- TTL过期
- 缓存命中/未命中
"""

import hashlib
import time
from unittest.mock import Mock, patch, MagicMock
import pytest


class TestCacheKeyGenerator:
    """缓存键名生成器测试"""

    def test_tender_list_key_format(self):
        """测试招标列表缓存键格式"""
        # 导入键生成器
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings_test')

        from apps.core.cache.keys import tender_list

        # 测试基本分页
        key = tender_list(page=1, filters={})
        assert key.startswith('tenders:list:')

        # 测试带过滤条件
        filters = {'region': '北京', 'industry': '建筑'}
        key = tender_list(page=1, filters=filters)
        assert 'tenders:list:1:' in key

        # 测试不同页码
        key_page1 = tender_list(page=1, filters={})
        key_page2 = tender_list(page=2, filters={})
        assert key_page1 != key_page2

    def test_tender_detail_key_format(self):
        """测试招标详情缓存键格式"""
        from apps.core.cache.keys import tender_detail

        key = tender_detail(123)
        assert key == 'tender:123:detail'

    def test_tender_stats_key(self):
        """测试统计数据缓存键"""
        from apps.core.cache.keys import tender_stats

        key = tender_stats()
        assert key == 'tenders:stats'

    def test_search_results_key(self):
        """测试搜索结果缓存键"""
        from apps.core.cache.keys import search_results

        key = search_results('招标公告')
        assert key.startswith('search:')

    def test_region_distribution_key(self):
        """测试地区分布缓存键"""
        from apps.core.cache.keys import region_distribution

        key = region_distribution()
        assert key == 'stats:regions'

    def test_industry_distribution_key(self):
        """测试行业分布缓存键"""
        from apps.core.cache.keys import industry_distribution

        key = industry_distribution()
        assert key == 'stats:industries'


class TestCacheConfig:
    """缓存配置测试"""

    def test_ttl_constants_exist(self):
        """测试TTL常量定义"""
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings_test')

        from apps.core.cache.config import (
            TENDER_LIST_TTL,
            TENDER_DETAIL_TTL,
            STATS_TTL,
            SEARCH_TTL,
        )

        assert TENDER_LIST_TTL == 300
        assert TENDER_DETAIL_TTL == 600
        assert STATS_TTL == 1800
        assert SEARCH_TTL == 120


class TestCacheDecorators:
    """缓存装饰器测试"""

    @pytest.fixture
    def mock_cache(self):
        """模拟缓存对象"""
        with patch('apps.core.cache.decorators.cache') as mock:
            yield mock

    def test_cached_decorator_stores_result(self, mock_cache):
        """测试缓存装饰器存储结果"""
        mock_cache.get.return_value = None

        from apps.core.cache.decorators import cached

        @cached(ttl=300)
        def expensive_function():
            return 'computed result'

        result = expensive_function()

        assert result == 'computed result'
        mock_cache.set.assert_called_once()

    def test_cached_decorator_returns_cached(self, mock_cache):
        """测试缓存装饰器返回缓存结果"""
        cached_value = 'cached result'
        mock_cache.get.return_value = cached_value

        from apps.core.cache.decorators import cached

        @cached(ttl=300)
        def expensive_function():
            return 'computed result'

        result = expensive_function()

        assert result == cached_value
        mock_cache.get.assert_called_once()
        mock_cache.set.assert_not_called()

    def test_cache_evict_decorator(self):
        """测试缓存清除装饰器"""
        with patch('apps.core.cache.decorators.cache') as mock_cache:
            from apps.core.cache.decorators import cache_evict

            # 提供delete_pattern方法以便测试
            mock_cache.delete_pattern.return_value = True

            @cache_evict(key_pattern='tenders:123')
            def modify_function():
                return 'modified'

            result = modify_function()

            assert result == 'modified'
            mock_cache.delete.assert_called_with('tenders:123')

    def test_cache_page_decorator(self):
        """测试页面缓存装饰器"""
        from django.test import RequestFactory
        from django.http import HttpResponse
        from apps.core.cache.decorators import cache_page

        with patch('apps.core.cache.decorators.cache') as mock_cache:
            mock_cache.get.return_value = None

            @cache_page(ttl=60)
            def view_func(request):
                return HttpResponse('content')

            factory = RequestFactory()
            request = factory.get('/test/')
            response = view_func(request)

            assert response.status_code == 200


class TestTenderCacheManager:
    """招标缓存管理器测试"""

    @pytest.fixture
    def cache_manager(self):
        """创建缓存管理器实例"""
        from apps.core.cache.managers import TenderCacheManager
        return TenderCacheManager()

    @pytest.fixture
    def mock_cache(self):
        """模拟缓存"""
        with patch('apps.core.cache.managers.cache') as mock:
            yield mock

    def test_cache_tender_list(self, cache_manager, mock_cache):
        """测试缓存招标列表"""
        data = [{'id': 1, 'title': '招标公告'}]
        mock_cache.set.return_value = True

        result = cache_manager.cache_tender_list(page=1, filters={}, data=data)

        assert result is True
        mock_cache.set.assert_called_once()

    def test_get_tender_list_cache_hit(self, cache_manager, mock_cache):
        """测试获取招标列表-缓存命中"""
        cached_data = [{'id': 1, 'title': '招标公告'}]
        mock_cache.get.return_value = cached_data

        result = cache_manager.get_tender_list(page=1, filters={})

        assert result == cached_data
        mock_cache.get.assert_called_once()

    def test_get_tender_list_cache_miss(self, cache_manager, mock_cache):
        """测试获取招标列表-缓存未命中"""
        mock_cache.get.return_value = None

        result = cache_manager.get_tender_list(page=1, filters={})

        assert result is None

    def test_invalidate_tender_list(self, cache_manager, mock_cache):
        """测试清除招标列表缓存"""
        mock_cache.delete.return_value = True

        result = cache_manager.invalidate_tender_list()

        assert result is True

    def test_cache_tender_detail(self, cache_manager, mock_cache):
        """测试缓存招标详情"""
        data = {'id': 1, 'title': '招标公告', 'content': '详情内容'}
        mock_cache.set.return_value = True

        result = cache_manager.cache_tender_detail(tender_id=1, data=data)

        assert result is True
        mock_cache.set.assert_called_once()

    def test_get_tender_detail(self, cache_manager, mock_cache):
        """测试获取招标详情"""
        cached_data = {'id': 1, 'title': '招标公告'}
        mock_cache.get.return_value = cached_data

        result = cache_manager.get_tender_detail(tender_id=1)

        assert result == cached_data

    def test_invalidate_tender_detail(self, cache_manager, mock_cache):
        """测试清除招标详情缓存"""
        mock_cache.delete.return_value = True

        result = cache_manager.invalidate_tender_detail(tender_id=123)

        assert result is True
        mock_cache.delete.assert_called_with('tender:123:detail')

    def test_cache_tender_stats(self, cache_manager, mock_cache):
        """测试缓存统计数据"""
        stats = {'total': 100, 'pending': 50}
        mock_cache.set.return_value = True

        result = cache_manager.cache_tender_stats(stats)

        assert result is True

    def test_get_tender_stats(self, cache_manager, mock_cache):
        """测试获取统计数据"""
        stats = {'total': 100, 'pending': 50}
        mock_cache.get.return_value = stats

        result = cache_manager.get_tender_stats()

        assert result == stats


class TestCacheExpiration:
    """缓存过期测试"""

    def test_ttl_settings(self):
        """测试TTL设置正确"""
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings_test')

        from apps.core.cache.config import (
            TENDER_LIST_TTL,
            TENDER_DETAIL_TTL,
            STATS_TTL,
            SEARCH_TTL,
        )

        # 验证TTL值符合预期
        assert TENDER_LIST_TTL > 0
        assert TENDER_DETAIL_TTL > TENDER_LIST_TTL
        assert STATS_TTL > TENDER_DETAIL_TTL
        assert SEARCH_TTL < TENDER_LIST_TTL

    def test_cache_key_consistency(self):
        """测试缓存键一致性"""
        from apps.core.cache.keys import tender_list, tender_detail

        # 相同参数应生成相同键
        key1 = tender_list(page=1, filters={'a': '1'})
        key2 = tender_list(page=1, filters={'a': '1'})
        assert key1 == key2

        # 不同参数应生成不同键
        key3 = tender_list(page=2, filters={'a': '1'})
        assert key1 != key3


class TestConcurrentCache:
    """并发缓存测试"""

    def test_concurrent_cache_operations(self):
        """测试并发缓存操作"""
        from django.core.cache import cache
        import threading

        results = []

        def cache_operation(thread_id):
            key = f'test:thread:{thread_id}'
            cache.set(key, f'result_{thread_id}', 60)
            value = cache.get(key)
            results.append(value)

        threads = [threading.Thread(target=cache_operation, args=(i,)) for i in range(5)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(results) == 5


class TestEdgeCases:
    """边界情况测试"""

    def test_empty_filters(self):
        """测试空过滤条件"""
        from apps.core.cache.keys import tender_list

        key = tender_list(page=1, filters={})
        assert key is not None
        assert len(key) > 0

    def test_none_filters(self):
        """测试None过滤条件"""
        from apps.core.cache.keys import tender_list

        key = tender_list(page=1, filters=None)
        assert key is not None

    def test_special_characters_in_query(self):
        """测试搜索关键词中的特殊字符"""
        from apps.core.cache.keys import search_results

        # 测试包含特殊字符的搜索
        key = search_results('招标公告 <>&"\'测试')
        assert key.startswith('search:')

    def test_large_page_number(self):
        """测试大页码"""
        from apps.core.cache.keys import tender_list

        key = tender_list(page=10000, filters={})
        assert '10000' in key

    def test_zero_page(self):
        """测试零页码"""
        from apps.core.cache.keys import tender_list

        # 应该处理零页码
        key = tender_list(page=0, filters={})
        assert key is not None


class TestCacheKeyGeneratorExtra:
    """额外的缓存键生成器测试"""

    def test_user_preferences_key(self):
        """测试用户偏好缓存键"""
        from apps.core.cache.keys import user_preferences

        key = user_preferences(user_id=123)
        assert key == 'user:123:preferences'

    def test_notification_list_key(self):
        """测试通知列表缓存键"""
        from apps.core.cache.keys import notification_list

        key = notification_list(user_id=123, page=1)
        assert 'notifications:123:page:1' in key

    def test_dashboard_stats_key(self):
        """测试仪表盘统计缓存键"""
        from apps.core.cache.keys import dashboard_stats

        key = dashboard_stats(user_id=456)
        assert key == 'dashboard:456:stats'

    def test_complex_filters(self):
        """测试复杂过滤条件"""
        from apps.core.cache.keys import tender_list

        filters = {
            'region': '北京',
            'industry': '建筑',
            'status': 'pending',
            'min_amount': 100000,
            'max_amount': 5000000,
        }
        key = tender_list(page=1, filters=filters)
        assert key.startswith('tenders:list:')
        assert ':1:' in key


class TestDecoratorsExtra:
    """额外的装饰器测试"""

    def test_cached_decorator_with_args(self):
        """测试带参数的缓存装饰器"""
        with patch('apps.core.cache.decorators.cache') as mock_cache:
            mock_cache.get.return_value = None

            from apps.core.cache.decorators import cached

            call_count = [0]

            @cached(ttl=600, key_prefix='custom_prefix')
            def expensive_operation(x):
                call_count[0] += 1
                return x * 2

            result = expensive_operation(5)
            assert result == 10
            assert call_count[0] == 1
            mock_cache.set.assert_called_once()

    def test_cached_decorator_caches_different_args(self):
        """测试不同参数的缓存"""
        with patch('apps.core.cache.decorators.cache') as mock_cache:
            mock_cache.get.return_value = None

            from apps.core.cache.decorators import cached

            @cached(ttl=300)
            def add(a, b):
                return a + b

            # 不同的参数组合应该有不同的缓存键
            result1 = add(1, 2)
            result2 = add(3, 4)
            result3 = add(1, 2)  # 应该使用缓存

            assert result1 == 3
            assert result2 == 7
            assert result3 == 3

            # 第一次调用时get返回None，所以3个调用都会set
            # 这是因为每次调用函数时，get总是返回None
            assert mock_cache.set.call_count >= 2

    def test_cached_method_decorator(self):
        """测试类方法缓存装饰器"""
        with patch('apps.core.cache.decorators.cache') as mock_cache:
            mock_cache.get.return_value = None

            from apps.core.cache.decorators import cached_method

            class MyService:
                @cached_method(ttl=300)
                def compute(self, value):
                    return value * 3

            service = MyService()
            result = service.compute(10)
            assert result == 30
            mock_cache.set.assert_called_once()

    def test_cached_method_decorator_returns_cached(self):
        """测试类方法缓存装饰器返回缓存"""
        with patch('apps.core.cache.decorators.cache') as mock_cache:
            cached_value = 'from cache'
            mock_cache.get.return_value = cached_value

            from apps.core.cache.decorators import cached_method

            class MyService:
                @cached_method(ttl=300)
                def compute(self, value):
                    return 'computed'

            service = MyService()
            result = service.compute(10)
            assert result == cached_value
            mock_cache.get.assert_called_once()


class TestCacheManagerExtra:
    """额外的缓存管理器测试"""

    @pytest.fixture
    def mock_cache_full(self):
        """模拟缓存"""
        with patch('apps.core.cache.managers.cache') as mock:
            yield mock

    def test_cache_search_results(self, mock_cache_full):
        """测试缓存搜索结果"""
        from apps.core.cache.managers import TenderCacheManager

        manager = TenderCacheManager()
        mock_cache_full.set.return_value = True

        results = [{'id': 1, 'title': '测试'}]
        result = manager.cache_search_results('测试', results)

        assert result is True

    def test_get_search_results(self, mock_cache_full):
        """测试获取搜索结果缓存"""
        from apps.core.cache.managers import TenderCacheManager

        manager = TenderCacheManager()
        cached_results = [{'id': 1, 'title': '测试'}]
        mock_cache_full.get.return_value = cached_results

        result = manager.get_search_results('测试')
        assert result == cached_results

    def test_cache_region_distribution(self, mock_cache_full):
        """测试缓存地区分布"""
        from apps.core.cache.managers import TenderCacheManager

        manager = TenderCacheManager()
        mock_cache_full.set.return_value = True

        data = {'北京': 100, '上海': 80}
        result = manager.cache_region_distribution(data)

        assert result is True

    def test_get_region_distribution(self, mock_cache_full):
        """测试获取地区分布缓存"""
        from apps.core.cache.managers import TenderCacheManager

        manager = TenderCacheManager()
        cached_data = {'北京': 100, '上海': 80}
        mock_cache_full.get.return_value = cached_data

        result = manager.get_region_distribution()
        assert result == cached_data

    def test_cache_industry_distribution(self, mock_cache_full):
        """测试缓存行业分布"""
        from apps.core.cache.managers import TenderCacheManager

        manager = TenderCacheManager()
        mock_cache_full.set.return_value = True

        data = {'建筑': 50, '医疗': 30}
        result = manager.cache_industry_distribution(data)

        assert result is True

    def test_get_industry_distribution(self, mock_cache_full):
        """测试获取行业分布缓存"""
        from apps.core.cache.managers import TenderCacheManager

        manager = TenderCacheManager()
        cached_data = {'建筑': 50, '医疗': 30}
        mock_cache_full.get.return_value = cached_data

        result = manager.get_industry_distribution()
        assert result == cached_data

    def test_invalidate_tender_stats(self, mock_cache_full):
        """测试清除统计数据缓存"""
        from apps.core.cache.managers import TenderCacheManager

        manager = TenderCacheManager()
        mock_cache_full.delete.return_value = True

        result = manager.invalidate_tender_stats()
        assert result is True

    def test_invalidate_all(self, mock_cache_full):
        """测试清除所有缓存"""
        from apps.core.cache.managers import TenderCacheManager

        manager = TenderCacheManager()

        result = manager.invalidate_all()
        assert result is True

    def test_get_cache_manager_singleton(self):
        """测试获取缓存管理器单例"""
        from apps.core.cache.managers import get_cache_manager, TenderCacheManager

        manager1 = get_cache_manager()
        manager2 = get_cache_manager()

        assert isinstance(manager1, TenderCacheManager)
        assert manager1 is manager2

    def test_custom_ttl(self, mock_cache_full):
        """测试自定义TTL"""
        from apps.core.cache.managers import TenderCacheManager

        manager = TenderCacheManager()
        mock_cache_full.set.return_value = True

        data = [{'id': 1}]
        result = manager.cache_tender_list(page=1, filters={}, data=data, ttl=120)

        assert result is True
        # 验证被调用了
        mock_cache_full.set.assert_called_once()
        # 验证调用包含ttl参数
        call_args = mock_cache_full.set.call_args
        # 参数可以是位置参数或关键字参数
        args, kwargs = call_args
        # 检查timeout在kwargs中或作为位置参数
        assert 120 in args or kwargs.get('timeout') == 120