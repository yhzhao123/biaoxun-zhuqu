"""
Performance Testing Module
Task 070: Performance Testing Configuration
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class SLAThresholds:
    """SLA thresholds for performance testing"""
    p95_response_time_ms: int = 500  # 95th percentile < 500ms
    p99_response_time_ms: int = 1000  # 99th percentile < 1000ms
    error_rate_percent: float = 1.0  # Error rate < 1%
    throughput_rps: int = 100  # Requests per second


@dataclass
class LoadTestConfig:
    """Configuration for load testing"""
    concurrent_users: int = 100
    ramp_up_seconds: int = 60
    duration_seconds: int = 300
    target_rps: int = 100


@dataclass
class StressTestConfig:
    """Configuration for stress testing"""
    max_concurrent_users: int = 600
    ramp_up_seconds: int = 120
    step_users: int = 100
    step_duration_seconds: int = 60


@dataclass
class SpikeTestConfig:
    """Configuration for spike testing"""
    base_users: int = 100
    spike_users: int = 1000
    spike_duration_seconds: int = 60
    cooldown_seconds: int = 120


@dataclass
class SoakTestConfig:
    """Configuration for soak testing"""
    concurrent_users: int = 200
    duration_hours: int = 1
    ramp_up_seconds: int = 300


class PerformanceConfig:
    """Main performance test configuration"""

    # SLA thresholds
    SLA = SLAThresholds()

    # Test configurations
    LOAD = LoadTestConfig()
    STRESS = StressTestConfig()
    SPIKE = SpikeTestConfig()
    SOAK = SoakTestConfig()

    # API endpoints to test
    API_ENDPOINTS = {
        'tender_list': '/api/tenders/',
        'tender_detail': '/api/tenders/{id}/',
        'search': '/api/tenders/search/',
        'stats': '/api/tenders/stats/',
        'dashboard': '/api/dashboard/',
        'regions': '/api/regions/',
        'industries': '/api/industries/',
    }

    @classmethod
    def get_endpoint_url(cls, name: str, **kwargs) -> Optional[str]:
        """Get endpoint URL with optional formatting"""
        endpoint = cls.API_ENDPOINTS.get(name)
        if endpoint and kwargs:
            return endpoint.format(**kwargs)
        return endpoint
