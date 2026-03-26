"""
Performance Test Configuration
SLA thresholds and test parameters for performance testing.
"""

# API Performance Thresholds (in milliseconds)
API_THRESHOLDS = {
    'p95_response_time': 500,  # p95 < 500ms
    'p99_response_time': 1000,  # p99 < 1000ms
    'search_p95': 800,  # Search API p95 < 800ms
    'error_rate': 1.0,  # < 1% error rate
}

# Load Test Parameters
LOAD_TEST_CONFIG = {
    'normal_users': 100,  # Normal concurrent users
    'ramp_up_time': 30,  # seconds
    'test_duration': 300,  # 5 minutes
    'spawn_rate': 10,  # users/second
}

# Stress Test Parameters
STRESS_TEST_CONFIG = {
    'max_users': 600,  # Maximum concurrent users
    'ramp_up_time': 60,
    'test_duration': 600,  # 10 minutes
    'spawn_rate': 20,
}

# Spike Test Parameters
SPIKE_TEST_CONFIG = {
    'baseline_users': 100,
    'spike_users': 1000,
    'ramp_up_time': 10,  # Quick spike
    'hold_time': 60,  # Hold spike for 1 minute
    'recovery_time': 120,  # Recovery period
}

# Soak Test Parameters
SOAK_TEST_CONFIG = {
    'users': 200,
    'duration': 3600,  # 1 hour
    'spawn_rate': 5,
}

# Database Thresholds
DB_THRESHOLDS = {
    'query_time': 100,  # < 100ms per query
    'cache_hit_rate': 80,  # > 80% cache hit rate
}

# Target API Endpoints for Testing
TARGET_ENDPOINTS = [
    '/api/v1/tenders/',
    '/api/v1/tenders/{id}/',
    '/api/v1/statistics/',
    '/api/v1/statistics/trend/',
    '/api/v1/statistics/budget/',
    '/api/v1/statistics/top-tenderers/',
    '/api/v1/opportunities/',
    '/api/v1/opportunities/high-value/',
    '/api/v1/opportunities/urgent/',
    '/api/v1/reports/daily/',
    '/api/v1/reports/weekly/',
]

# Test Data Configuration
TEST_DATA_CONFIG = {
    'tenders_count': 1000,  # Number of tenders to create for testing
    'tenderers_count': 100,  # Number of tenderers
    'warm_up_requests': 10,  # Warm up requests before testing
}