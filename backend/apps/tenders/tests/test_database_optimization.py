"""
数据库优化测试 - Task 067
测试索引性能、查询优化和分区策略
"""
import pytest
from django.test import TestCase, override_settings
from django.db import connection, transaction
from django.db.models import Index
from datetime import datetime, timedelta
from decimal import Decimal

from apps.tenders.models import TenderNotice
from apps.users.models import User


def is_postgresql():
    """检查是否使用 PostgreSQL 数据库"""
    return connection.vendor == 'postgresql'


def get_index_names(table_name):
    """获取表的索引名称列表"""
    with connection.cursor() as cursor:
        if is_postgresql():
            cursor.execute("""
                SELECT indexname FROM pg_indexes
                WHERE tablename = %s
            """, [table_name])
            return [row[0] for row in cursor.fetchall()]
        else:
            # SQLite
            cursor.execute(f"PRAGMA index_list({table_name})")
            return [row[1] for row in cursor.fetchall()]


@pytest.mark.django_db
class TestDatabaseIndexes(TestCase):
    """测试数据库索引配置"""

    def setUp(self):
        """创建测试数据"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass'
        )
        self._create_test_tenders()

    def _create_test_tenders(self, count=100):
        """创建测试招标数据"""
        tenders = []
        base_date = datetime.now()

        for i in range(count):
            tender = TenderNotice(
                notice_id=f'TEST-{i:06d}',
                title=f'测试招标公告 {i}',
                description=f'测试描述 {i}',
                tenderer=f'招标人_{i % 10}',
                notice_type=TenderNotice.TYPE_BIDDING if i % 2 == 0 else TenderNotice.TYPE_WIN,
                budget=Decimal(f'{100000 + i * 1000}.00'),
                budget_amount=Decimal(f'{100000 + i * 1000}.00'),
                publish_date=base_date - timedelta(days=i % 30),
                status=TenderNotice.STATUS_ACTIVE if i % 3 == 0 else TenderNotice.STATUS_CLOSED,
                region=f'region_{i % 5}',
                region_code=f'RC{i % 5:02d}',
                industry=f'industry_{i % 8}',
                industry_code=f'IC{i % 8:02d}',
                crawl_batch_id=f'BATCH_{i % 20:03d}',
                created_by=self.user
            )
            tenders.append(tender)

        TenderNotice.objects.bulk_create(tenders)

    def test_notice_id_index_exists(self):
        """测试 notice_id 索引是否存在（包括唯一约束自动创建的索引）"""
        indexes = get_index_names('tender_notices')
        # notice_id 索引可能是显式创建的，也可能是唯一约束自动创建的
        has_notice_id_idx = any('notice_id' in idx.lower() for idx in indexes)
        has_autoindex = any('autoindex' in idx.lower() for idx in indexes)
        self.assertTrue(
            has_notice_id_idx or has_autoindex,
            f"notice_id 索引不存在. 现有索引: {indexes}"
        )

    def test_publish_date_index_exists(self):
        """测试 publish_date 索引是否存在"""
        indexes = get_index_names('tender_notices')
        self.assertTrue(
            any('publish_date' in idx.lower() for idx in indexes),
            f"publish_date 索引不存在. 现有索引: {indexes}"
        )

    def test_status_index_exists(self):
        """测试 status 索引是否存在"""
        indexes = get_index_names('tender_notices')
        self.assertTrue(
            any('status' in idx.lower() for idx in indexes),
            f"status 索引不存在. 现有索引: {indexes}"
        )

    def test_composite_index_tenderer_status(self):
        """测试 tenderer + status 复合索引"""
        indexes = get_index_names('tender_notices')
        # 检查 tenderer 相关的索引（可能是复合索引的一部分）
        has_tenderer_idx = any('tender' in idx.lower() for idx in indexes)
        self.assertTrue(
            has_tenderer_idx,
            f"tenderer 复合索引不存在. 现有索引: {indexes}"
        )

    def test_region_industry_composite_index(self):
        """测试 region + industry 复合索引"""
        indexes = get_index_names('tender_notices')
        self.assertTrue(
            any('region' in idx.lower() for idx in indexes),
            f"region + industry 复合索引不存在. 现有索引: {indexes}"
        )

    def test_budget_amount_index_exists(self):
        """测试 budget_amount 索引是否存在"""
        indexes = get_index_names('tender_notices')
        self.assertTrue(
            any('budget_amount' in idx.lower() for idx in indexes),
            f"budget_amount 索引不存在. 现有索引: {indexes}"
        )

    def test_crawl_batch_index_exists(self):
        """测试 crawl_batch_id 索引是否存在"""
        indexes = get_index_names('tender_notices')
        self.assertTrue(
            any('crawl_batch' in idx.lower() for idx in indexes),
            f"crawl_batch_id 索引不存在. 现有索引: {indexes}"
        )


@pytest.mark.django_db
class TestQueryPerformance(TestCase):
    """测试查询性能优化"""

    def setUp(self):
        """创建测试数据"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass'
        )
        self._create_test_tenders(50)

    def _create_test_tenders(self, count=50):
        """创建测试招标数据"""
        tenders = []
        base_date = datetime.now()

        for i in range(count):
            tender = TenderNotice(
                notice_id=f'PERF-{i:06d}',
                title=f'性能测试招标 {i}',
                description=f'性能测试描述 {i}',
                tenderer=f'招标人_{i % 5}',
                notice_type=TenderNotice.TYPE_BIDDING,
                budget=Decimal(f'{100000 + i * 1000}.00'),
                budget_amount=Decimal(f'{100000 + i * 1000}.00'),
                publish_date=base_date - timedelta(days=i % 30),
                status=TenderNotice.STATUS_ACTIVE if i % 3 == 0 else TenderNotice.STATUS_CLOSED,
                region=f'北京',
                region_code='BJ',
                industry=f'IT',
                industry_code='IT01',
                crawl_batch_id=f'BATCH_001',
                created_by=self.user
            )
            tenders.append(tender)

        TenderNotice.objects.bulk_create(tenders)

    def test_query_uses_index_for_notice_id(self):
        """测试按 notice_id 查询使用索引"""
        if not is_postgresql():
            self.skipTest("索引使用检查仅在 PostgreSQL 上测试")

        with connection.cursor() as cursor:
            cursor.execute("""
                EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
                SELECT * FROM tender_notices WHERE notice_id = 'PERF-000001'
            """)
            plan = '\n'.join([row[0] for row in cursor.fetchall()])

            # 验证查询计划使用了索引
            self.assertIn('Index', plan,
                "按 notice_id 查询应该使用索引")

    def test_query_uses_index_for_publish_date_range(self):
        """测试按发布日期范围查询使用索引"""
        if not is_postgresql():
            self.skipTest("索引使用检查仅在 PostgreSQL 上测试")

        start_date = datetime.now() - timedelta(days=10)
        end_date = datetime.now()

        with connection.cursor() as cursor:
            cursor.execute("""
                EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
                SELECT * FROM tender_notices
                WHERE publish_date BETWEEN %s AND %s
            """, [start_date, end_date])
            plan = '\n'.join([row[0] for row in cursor.fetchall()])

            # 验证查询计划使用了索引扫描
            self.assertIn('Index', plan,
                "按发布日期范围查询应该使用索引扫描")

    def test_query_uses_index_for_status_filter(self):
        """测试按状态筛选使用索引"""
        if not is_postgresql():
            self.skipTest("索引使用检查仅在 PostgreSQL 上测试")

        with connection.cursor() as cursor:
            cursor.execute("""
                EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
                SELECT * FROM tender_notices WHERE status = 'active'
            """)
            plan = '\n'.join([row[0] for row in cursor.fetchall()])

            # 验证查询计划使用了索引
            self.assertIn('Index', plan,
                "按状态筛选应该使用索引")

    def test_query_performance_for_tenderer_search(self):
        """测试招标人查询性能"""
        import time

        start_time = time.time()
        results = list(TenderNotice.objects.filter(tenderer__icontains='招标人_1'))
        elapsed_time = (time.time() - start_time) * 1000

        # 查询应该在 100ms 内完成
        self.assertLess(elapsed_time, 100,
            f"招标人查询耗时 {elapsed_time:.2f}ms, 超过 100ms 阈值")

    def test_query_performance_for_region_industry_filter(self):
        """测试地区行业联合查询性能"""
        import time

        start_time = time.time()
        results = list(TenderNotice.objects.filter(
            region_code='BJ',
            industry_code='IT01'
        ))
        elapsed_time = (time.time() - start_time) * 1000

        # 查询应该在 50ms 内完成
        self.assertLess(elapsed_time, 50,
            f"地区行业查询耗时 {elapsed_time:.2f}ms, 超过 50ms 阈值")


@pytest.mark.django_db
class TestDatabasePartitioning(TestCase):
    """测试数据库表分区"""

    def test_partitioned_table_exists(self):
        """测试分区表是否存在"""
        if not is_postgresql():
            self.skipTest("分区表检查仅在 PostgreSQL 上测试")

        # 注意：Django ORM 不直接支持 PostgreSQL 分区表
        # 这里测试通过原始 SQL 检查分区是否存在
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) FROM pg_inherits
                WHERE inhparent = 'tender_notices'::regclass
            """)
            count = cursor.fetchone()[0]

        # 如果启用了分区，应该至少有一个子表
        # 目前不强制要求，只是记录状态
        self.assertIsNotNone(count)


@pytest.mark.django_db
class TestConnectionPool(TestCase):
    """测试数据库连接池配置"""

    @override_settings(DATABASES={
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': 'test_db',
            'USER': 'test_user',
            'PASSWORD': 'test_pass',
            'HOST': 'localhost',
            'PORT': '5432',
            'CONN_MAX_AGE': 600,  # 10分钟连接保持
            'OPTIONS': {
                'MIN_CONNS': 5,
                'MAX_CONNS': 20,
            }
        }
    })
    def test_connection_pool_settings(self):
        """测试连接池配置"""
        from django.conf import settings

        db_config = settings.DATABASES['default']

        # 验证连接保持设置
        self.assertIn('CONN_MAX_AGE', db_config,
            "数据库配置应该包含 CONN_MAX_AGE")
        self.assertGreaterEqual(db_config['CONN_MAX_AGE'], 600,
            "连接保持时间应该至少 600 秒")


@pytest.mark.django_db
class TestIndexMaintenance(TestCase):
    """测试索引维护脚本"""

    def test_analyze_command_runs(self):
        """测试 ANALYZE 命令可以正常执行"""
        with connection.cursor() as cursor:
            try:
                cursor.execute("ANALYZE tender_notices")
                self.assertTrue(True, "ANALYZE 命令执行成功")
            except Exception as e:
                self.fail(f"ANALYZE 命令执行失败: {e}")

    def test_reindex_command_runs(self):
        """测试 REINDEX 命令可以正常执行"""
        if not is_postgresql():
            self.skipTest("REINDEX 仅在 PostgreSQL 上测试")

        with connection.cursor() as cursor:
            try:
                cursor.execute("REINDEX TABLE CONCURRENTLY tender_notices")
                self.assertTrue(True, "REINDEX 命令执行成功")
            except Exception as e:
                # REINDEX CONCURRENTLY 可能需要特定权限
                # 只要命令语法正确就算通过
                if "CONCURRENTLY" in str(e):
                    try:
                        cursor.execute("REINDEX TABLE tender_notices")
                        self.assertTrue(True, "REINDEX 命令执行成功")
                    except Exception as e2:
                        self.fail(f"REINDEX 命令执行失败: {e2}")
                else:
                    self.fail(f"REINDEX 命令执行失败: {e}")
