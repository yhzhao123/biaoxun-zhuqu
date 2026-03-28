"""
Test script for TenderOrchestratorV2 (4 Agent Teams)
"""
import asyncio
import os
import logging

logging.basicConfig(level=logging.INFO)

# Set required environment variables before Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
os.environ.setdefault('SECRET_KEY', 'test-secret-key-for-testing-only')
os.environ.setdefault('DATABASE_URL', 'sqlite:///test_db.sqlite3')  # Use SQLite for testing
os.environ.setdefault('POSTGRES_PASSWORD', 'test')
os.environ.setdefault('REDIS_URL', 'redis://localhost:6379')

import django
from django.conf import settings

# Override database settings to use SQLite
if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': 'test_db.sqlite3'}},
        INSTALLED_APPS=[
            'django.contrib.contenttypes',
            'django.contrib.auth',
            'apps.crawler',
            'apps.tenders',
            'apps.llm',
        ],
        SECRET_KEY='test-secret-key-for-testing-only',
        USE_TZ=True,
    )
else:
    settings.DATABASES['default'] = {'ENGINE': 'django.db.backends.sqlite3', 'NAME': 'test_db.sqlite3'}

django.setup()

# Create tables
from django.core.management import call_command
call_command('migrate', '--run-syncdb', verbosity=0)

from apps.crawler.agents import TenderOrchestratorV2, OrchestratorV2Config
from apps.crawler.models import CrawlSource


async def test_orchestrator_v2():
    """Test Orchestrator V2 with 4 agent teams"""
    print("=" * 60)
    print("Testing TenderOrchestratorV2 (4 Agent Teams)")
    print("=" * 60)

    # 配置
    config = OrchestratorV2Config(
        max_concurrent_requests=3,
        max_concurrent_llm_calls=1,  # 保守设置避免429
        max_concurrent_details=5,
        request_delay=1.5,
        llm_delay=1.0,
        max_retries=3,
        base_delay=2.0,
        cache_enabled=True,
        cache_ttl=7200,
        use_list_data=True,
        use_regex_preprocessing=True,
        batch_size=10,
        max_items_per_source=20,
    )

    # 创建编排器
    orchestrator = TenderOrchestratorV2(config)

    # 获取测试源
    source = await asyncio.to_thread(
        lambda: CrawlSource.objects.filter(id=3).first()
    )

    if not source:
        print("Source not found")
        return

    print(f"\nSource: {source.name}")
    print(f"URL: {source.url}")
    print(f"Config: {config}")

    try:
        # 执行提取
        print("\n" + "=" * 60)
        print("Starting extraction...")
        print("=" * 60)

        results = await orchestrator.extract_tenders(source, max_pages=2)

        print("\n" + "=" * 60)
        print(f"Extraction complete: {len(results)} items")
        print("=" * 60)

        # 显示结果
        for i, item in enumerate(results[:5], 1):
            print(f"\n[{i}] {item.title[:60]}...")
            print(f"    Tenderer: {item.tenderer or 'N/A'}")
            print(f"    Budget: {item.budget_amount}")
            print(f"    Method: {item.extraction_method}")
            print(f"    Confidence: {item.extraction_confidence:.2f}")

        # 最终统计
        print("\n" + "=" * 60)
        print("Final Statistics:")
        print("=" * 60)
        print(f"  Total items: {len(results)}")
        print(f"  Cache hits: {orchestrator.stats['cache_hits']}")
        print(f"  Cache misses: {orchestrator.stats['cache_misses']}")
        print(f"  LLM calls made: {orchestrator.stats['llm_calls_made']}")
        print(f"  LLM calls saved: {orchestrator.stats['llm_calls_saved']}")
        print(f"  Retries: {orchestrator.stats['retries']}")

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # 清理
        await orchestrator.close()


async def test_individual_agents():
    """Test individual agent teams"""
    print("\n" + "=" * 60)
    print("Testing Individual Agent Teams")
    print("=" * 60)

    # 团队1: 并发控制
    from apps.crawler.agents import ConcurrencyControlAgent, ConcurrencyConfig
    concurrency_config = ConcurrencyConfig(
        max_concurrent_requests=5,
        max_concurrent_llm_calls=2,
    )
    concurrency_agent = ConcurrencyControlAgent(concurrency_config)
    print("\n[Team 1] ConcurrencyControlAgent initialized")
    print(f"  Max requests: {concurrency_config.max_concurrent_requests}")
    print(f"  Max LLM calls: {concurrency_config.max_concurrent_llm_calls}")

    # 团队2: 重试机制
    from apps.crawler.agents import RetryMechanismAgent, RetryConfig
    retry_config = RetryConfig(
        max_retries=3,
        base_delay=1.0,
    )
    retry_agent = RetryMechanismAgent(retry_config)
    print("\n[Team 2] RetryMechanismAgent initialized")
    print(f"  Max retries: {retry_config.max_retries}")
    print(f"  Base delay: {retry_config.base_delay}s")

    # 团队3: 缓存系统
    from apps.crawler.agents import CacheAgent, CacheConfig
    cache_config = CacheConfig(
        default_ttl=3600,
    )
    cache_agent = CacheAgent(cache_config)
    print("\n[Team 3] CacheAgent initialized")
    print(f"  Default TTL: {cache_config.default_ttl}s")

    # 测试缓存
    test_url = "https://example.com/test"
    cache_agent.set(test_url, {"test": "data"}, ttl=300)
    cached = cache_agent.get(test_url)
    print(f"  Cache test: {'PASS' if cached else 'FAIL'}")

    # 团队4: 字段优化
    from apps.crawler.agents import FieldOptimizationAgent, FieldOptimizationConfig
    field_config = FieldOptimizationConfig(
        required_fields=['title', 'tenderer', 'budget_amount'],
        use_regex_preprocessing=True,
    )
    field_agent = FieldOptimizationAgent(field_config)
    print("\n[Team 4] FieldOptimizationAgent initialized")
    print(f"  Required fields: {field_config.required_fields}")
    print(f"  Regex preprocessing: {field_config.use_regex_preprocessing}")

    print("\n" + "=" * 60)
    print("All 4 agent teams ready!")
    print("=" * 60)


if __name__ == '__main__':
    # 先测试各个智能体
    asyncio.run(test_individual_agents())

    # 再测试完整编排器
    print("\n\n")
    asyncio.run(test_orchestrator_v2())
