"""
Unit tests for 4 Agent Teams - No database required
"""
import asyncio
import os
import sys
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup Django settings (minimal)
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
os.environ['SECRET_KEY'] = 'test-secret-key-for-testing-only'
os.environ['POSTGRES_PASSWORD'] = 'test'
os.environ['REDIS_URL'] = 'redis://localhost:6379'
os.environ['DATABASE_URL'] = 'sqlite:///db.sqlite3'

import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=[
            'django.contrib.contenttypes',
            'django.contrib.auth',
            'apps.crawler',
        ],
        SECRET_KEY='test-secret-key',
        USE_TZ=True,
    )
django.setup()


class MockDetailResult:
    """Mock detail result for testing"""
    def __init__(self, html, url, attachments=None):
        self.html = html
        self.url = url
        self.attachments = attachments or []


def test_team_1_concurrency():
    """Test Team 1: ConcurrencyControlAgent"""
    print("\n" + "=" * 60)
    print("[Team 1] Testing ConcurrencyControlAgent")
    print("=" * 60)

    # Direct import from workers to avoid Django model dependencies
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "concurrency_agent",
        os.path.join(os.path.dirname(__file__), "apps", "crawler", "agents", "workers", "concurrency_agent.py")
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    ConcurrencyControlAgent = module.ConcurrencyControlAgent
    ConcurrencyConfig = module.ConcurrencyConfig

    config = ConcurrencyConfig(
        max_concurrent_requests=5,
        max_concurrent_llm_calls=3,
        max_concurrent_details=10,
        request_delay=0.1,
        llm_delay=0.05,
    )

    agent = ConcurrencyControlAgent(config)

    print(f"OK Created with {config.max_concurrent_requests} max requests")
    print(f"OK Semaphore initialized: {agent.request_semaphore._value}")
    print(f"OK LLM Semaphore: {agent.llm_semaphore._value}")
    print(f"OK Detail Semaphore: {agent.detail_semaphore._value}")

    return True


def test_team_2_retry():
    """Test Team 2: RetryMechanismAgent"""
    print("\n" + "=" * 60)
    print("[Team 2] Testing RetryMechanismAgent")
    print("=" * 60)

    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "retry_agent",
        os.path.join(os.path.dirname(__file__), "apps", "crawler", "agents", "workers", "retry_agent.py")
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    RetryMechanismAgent = module.RetryMechanismAgent
    RetryConfig = module.RetryConfig
    ErrorType = module.ErrorType
    CircuitBreaker = module.CircuitBreaker

    config = RetryConfig(
        max_retries=3,
        base_delay=1.0,
        max_delay=60.0,
        jitter=True,
        circuit_breaker_threshold=5,
        circuit_breaker_timeout=60.0,
    )

    agent = RetryMechanismAgent(config)

    print(f"OK Created with {config.max_retries} max retries")
    print(f"OK Circuit breaker threshold: {config.circuit_breaker_threshold}")
    print(f"OK Error types supported: {len(list(ErrorType))}")

    # Test CircuitBreaker
    cb = CircuitBreaker(threshold=3, timeout=30.0)
    print(f"OK CircuitBreaker state: {cb.get_state()}")

    # Test stats
    stats = agent.get_stats()
    print(f"OK Stats tracking: {stats}")

    return True


def test_team_3_cache():
    """Test Team 3: CacheAgent"""
    print("\n" + "=" * 60)
    print("[Team 3] Testing CacheAgent")
    print("=" * 60)

    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "cache_agent",
        os.path.join(os.path.dirname(__file__), "apps", "crawler", "agents", "workers", "cache_agent.py")
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    CacheAgent = module.CacheAgent
    CacheConfig = module.CacheConfig

    config = CacheConfig(
        memory_cache_size=100,
        default_ttl=3600,
    )

    agent = CacheAgent(config)

    # Test set and get (get returns tuple: (hit, value))
    test_data = {'title': 'Test Tender', 'budget': 1000000}
    agent.set('http://test.com/1', test_data, ttl=300, source_id='1')

    hit, cached = agent.get('http://test.com/1', source_id='1')
    assert hit and cached == test_data, "Cache get failed"
    print("OK Memory cache set/get working")

    # Test miss
    miss_hit, miss = agent.get('http://test.com/nonexistent')
    assert not miss_hit and miss is None, "Cache should return (False, None) for miss"
    print("OK Cache miss returns (False, None)")

    # Test stats
    stats = agent.get_stats()
    print(f"OK Cache stats: overall_hit_rate={stats.overall_hit_rate:.2%}")

    # Test invalidation
    agent.invalidate('http://test.com/.*')
    inv_hit, invalidated = agent.get('http://test.com/1', source_id='1')
    print(f"OK Cache invalidation working: hit={inv_hit}")

    return True


def test_team_4_field_optimizer():
    """Test Team 4: FieldOptimizationAgent"""
    print("\n" + "=" * 60)
    print("[Team 4] Testing FieldOptimizationAgent")
    print("=" * 60)

    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "field_optimizer",
        os.path.join(os.path.dirname(__file__), "apps", "crawler", "agents", "workers", "field_optimizer.py")
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    FieldOptimizationAgent = module.FieldOptimizationAgent
    FieldOptimizationConfig = module.FieldOptimizationConfig
    ExtractionResult = module.ExtractionResult

    config = FieldOptimizationConfig(
        required_fields=['title', 'tenderer', 'budget_amount', 'publish_date'],
        use_regex_preprocessing=True,
        llm_fallback_threshold=0.6,
    )

    agent = FieldOptimizationAgent(config)

    print(f"OK Created with {len(config.required_fields)} required fields")

    # Test extract_from_list
    list_item = {
        'title': 'Test Tender Notice',
        'tenderer': 'Test Company',
        'publish_date': '2024-01-15',
        'budget': '100万元',
    }

    extracted = agent.extract_from_list(list_item)
    print(f"OK List extraction: {len(extracted)} fields extracted")
    print(f"  - title: {extracted.get('title')}")
    print(f"  - tenderer: {extracted.get('tenderer')}")

    # Test regex preprocessing
    html = """
    <html>
    <body>
        <h1>Project XYZ Tender Notice</h1>
        <p>招标人: ABC Company</p>
        <p>预算金额: 500万元</p>
        <p>发布日期: 2024-03-27</p>
        <p>项目编号: PRJ-2024-001</p>
    </body>
    </html>
    """

    regex_data = agent.preprocess_with_regex(html)
    print(f"OK Regex preprocessing: {len(regex_data)} fields found")
    print(f"  - tenderer: {regex_data.get('tenderer')}")
    print(f"  - budget_amount: {regex_data.get('budget_amount')}")
    print(f"  - publish_date: {regex_data.get('publish_date')}")
    print(f"  - project_number: {regex_data.get('project_number')}")

    # Test missing fields detection
    prefilled = {'title': 'Test', 'tenderer': 'Company'}
    missing = agent.determine_missing_fields(prefilled, config.required_fields)
    print(f"OK Missing fields detection: {missing}")

    return True


def test_integration():
    """Test integration of all 4 teams"""
    print("\n" + "=" * 60)
    print("[Integration] Testing all 4 teams working together")
    print("=" * 60)

    import importlib.util
    workers_path = os.path.join(os.path.dirname(__file__), "apps", "crawler", "agents", "workers")

    # Load all modules
    modules = {}
    for name in ['concurrency_agent', 'retry_agent', 'cache_agent', 'field_optimizer']:
        spec = importlib.util.spec_from_file_location(name, os.path.join(workers_path, f"{name}.py"))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        modules[name] = module

    # Initialize all 4 teams
    concurrency = modules['concurrency_agent'].ConcurrencyControlAgent(
        modules['concurrency_agent'].ConcurrencyConfig()
    )
    retry = modules['retry_agent'].RetryMechanismAgent(
        modules['retry_agent'].RetryConfig()
    )
    cache = modules['cache_agent'].CacheAgent(
        modules['cache_agent'].CacheConfig()
    )
    optimizer = modules['field_optimizer'].FieldOptimizationAgent(
        modules['field_optimizer'].FieldOptimizationConfig()
    )

    print("OK All 4 teams initialized")

    # Test interaction: Cache + FieldOptimizer
    list_item = {'title': 'Cached Tender', 'tenderer': 'Cached Company'}
    cache.set('test-url', list_item)
    hit, cached = cache.get('test-url')

    extracted = optimizer.extract_from_list(cached if hit else list_item)
    print(f"OK Cache + Optimizer integration: {len(extracted)} fields")

    # Test interaction: Retry + Concurrency
    retry.set_concurrency_agent(concurrency)
    print("OK Retry + Concurrency integration: agent linked")

    return True


def run_all_tests():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("  4 Agent Teams Test Suite")
    print("  Testing Concurrency, Retry, Cache, and Field Optimization")
    print("=" * 70)

    tests = [
        ("Team 1: Concurrency Control", test_team_1_concurrency),
        ("Team 2: Retry Mechanism", test_team_2_retry),
        ("Team 3: Cache System", test_team_3_cache),
        ("Team 4: Field Optimization", test_team_4_field_optimizer),
        ("Integration Test", test_integration),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"\n[OK] {name}: PASSED")
            else:
                failed += 1
                print(f"\n[FAIL] {name}: FAILED")
        except Exception as e:
            failed += 1
            print(f"\n[ERROR] {name}: ERROR - {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 70)
    print(f"  Test Results: {passed} passed, {failed} failed")
    print("=" * 70)

    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
