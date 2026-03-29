"""
Test cases for error handling module

Tests:
1. Error classification (network errors, timeouts, API limits)
2. Smart retry mechanism (exponential backoff, max retries)
3. Circuit breaker pattern
4. Fallback strategy (switch to backup when primary fails)
"""
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from dataclasses import dataclass

from apps.crawler.tools.error_handling import (
    ErrorCategory,
    RetryableError,
    NonRetryableError,
    CircuitBreaker,
    CircuitBreakerState,
    RetryConfig,
    with_retry,
    with_circuit_breaker,
    FallbackStrategy,
    with_fallback,
    retry_with_backoff,
    is_retryable_error,
)


# ===================== Error Category Tests =====================

class TestErrorCategory:
    """Test error category classification"""

    def test_network_error_classification(self):
        """Network errors should be classified as retryable"""
        error = ConnectionError("Connection refused")
        category = ErrorCategory.classify(error)
        assert category == ErrorCategory.NETWORK

    def test_timeout_error_classification(self):
        """Timeout errors should be classified as retryable"""
        error = asyncio.TimeoutError("Request timed out")
        category = ErrorCategory.classify(error)
        assert category == ErrorCategory.TIMEOUT

    def test_rate_limit_error_classification(self):
        """HTTP 429 should be classified as rate limit"""
        # Simulate rate limit error
        error = RetryableError("Rate limit exceeded", status_code=429)
        category = ErrorCategory.classify(error)
        assert category == ErrorCategory.RATE_LIMIT

    def test_server_error_classification(self):
        """HTTP 5xx should be classified as retryable server error"""
        error = RetryableError("Internal server error", status_code=500)
        category = ErrorCategory.classify(error)
        assert category == ErrorCategory.SERVER_ERROR

    def test_client_error_classification(self):
        """HTTP 4xx (except 429) should be classified as non-retryable"""
        error = NonRetryableError("Not found", status_code=404)
        category = ErrorCategory.classify(error)
        assert category == ErrorCategory.CLIENT_ERROR

    def test_generic_error_classification(self):
        """Generic errors should be classified as unknown"""
        error = ValueError("Invalid input")
        category = ErrorCategory.classify(error)
        assert category == ErrorCategory.UNKNOWN


# ===================== Retry Config Tests =====================

class TestRetryConfig:
    """Test retry configuration"""

    def test_default_config(self):
        """Test default retry configuration"""
        config = RetryConfig()
        assert config.max_retries == 3
        assert config.base_delay == 1.0
        assert config.max_delay == 60.0
        assert config.exponential_base == 2
        assert config.jitter is True

    def test_custom_config(self):
        """Test custom retry configuration"""
        config = RetryConfig(
            max_retries=5,
            base_delay=2.0,
            max_delay=120.0,
            exponential_base=3,
            jitter=False,
        )
        assert config.max_retries == 5
        assert config.base_delay == 2.0
        assert config.max_delay == 120.0
        assert config.exponential_base == 3
        assert config.jitter is False

    def test_calculate_delay_exponential_backoff(self):
        """Test exponential backoff delay calculation"""
        config = RetryConfig(base_delay=1.0, exponential_base=2, jitter=False)

        # First retry: 1 * 2^0 = 1
        assert config.calculate_delay(0) == 1.0
        # Second retry: 1 * 2^1 = 2
        assert config.calculate_delay(1) == 2.0
        # Third retry: 1 * 2^2 = 4
        assert config.calculate_delay(2) == 4.0

    def test_calculate_delay_with_max_limit(self):
        """Test delay calculation with max limit"""
        config = RetryConfig(base_delay=1.0, max_delay=10.0, exponential_base=2, jitter=False)

        # Should not exceed max_delay
        assert config.calculate_delay(10) == 10.0


# ===================== Retryable Error Tests =====================

class TestRetryableError:
    """Test custom retryable error classes"""

    def test_retryable_error_creation(self):
        """Test creating a retryable error"""
        error = RetryableError("Rate limited", status_code=429)
        assert error.message == "Rate limited"
        assert error.status_code == 429
        assert error.is_retryable() is True

    def test_non_retryable_error_creation(self):
        """Test creating a non-retryable error"""
        error = NonRetryableError("Not found", status_code=404)
        assert error.message == "Not found"
        assert error.status_code == 404
        assert error.is_retryable() is False


# ===================== Circuit Breaker Tests =====================

class TestCircuitBreaker:
    """Test circuit breaker pattern"""

    @pytest.mark.asyncio
    async def test_circuit_closed_by_default(self):
        """Circuit breaker should be closed by default"""
        cb = CircuitBreaker(failure_threshold=3)
        assert cb.state == CircuitBreakerState.CLOSED

    @pytest.mark.asyncio
    async def test_circuit_opens_after_threshold(self):
        """Circuit should open after reaching failure threshold"""
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=1.0)

        # Fail 3 times
        for _ in range(3):
            await cb.record_failure()

        assert cb.state == CircuitBreakerState.OPEN

    @pytest.mark.asyncio
    async def test_circuit_resets_on_success(self):
        """Circuit should reset failure count on success"""
        cb = CircuitBreaker(failure_threshold=3)

        # Fail twice, then succeed
        await cb.record_failure()
        await cb.record_failure()
        await cb.record_success()

        # Should have 0 failures now
        await cb.record_failure()
        await cb.record_failure()
        # Should still be closed (2 failures < 3)
        assert cb.state == CircuitBreakerState.CLOSED

    @pytest.mark.asyncio
    async def test_circuit_half_open_after_recovery_timeout(self):
        """Circuit should go to half-open after recovery timeout"""
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=0.1)

        # Fail to open circuit
        await cb.record_failure()
        await cb.record_failure()
        assert cb.state == CircuitBreakerState.OPEN

        # Wait for recovery timeout
        await asyncio.sleep(0.2)

        # Check if circuit is half-open
        await cb.can_execute()
        # After waiting, should be able to try
        assert cb.state in [CircuitBreakerState.HALF_OPEN, CircuitBreakerState.CLOSED]

    @pytest.mark.asyncio
    async def test_circuit_prevents_execution_when_open(self):
        """Should prevent execution when circuit is open"""
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=1.0)

        # Open the circuit
        await cb.record_failure()
        await cb.record_failure()
        assert cb.state == CircuitBreakerState.OPEN

        # Should raise error when trying to execute
        with pytest.raises(Exception, match="Circuit breaker is OPEN"):
            await cb.record_failure()

    @pytest.mark.asyncio
    async def test_circuit_half_open_allows_one_request(self):
        """Half-open state should allow one request through"""
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=0.05)

        # Open the circuit
        await cb.record_failure()
        await cb.record_failure()

        # Wait and transition to half-open
        await asyncio.sleep(0.1)

        # Should allow execution in half-open
        can_exec = await cb.can_execute()
        assert can_exec is True


# ===================== With Retry Decorator Tests =====================

class TestWithRetry:
    """Test retry decorator"""

    @pytest.mark.asyncio
    async def test_successful_execution_no_retry(self):
        """Successful execution should not trigger retry"""
        mock_func = AsyncMock(return_value="success")
        decorated = with_retry(max_retries=3)(mock_func)

        result = await decorated()
        assert result == "success"
        assert mock_func.call_count == 1

    @pytest.mark.asyncio
    async def test_retry_on_retryable_error(self):
        """Should retry on retryable error"""
        mock_func = AsyncMock(side_effect=[
            RetryableError("Rate limited", status_code=429),
            RetryableError("Rate limited", status_code=429),
            "success"
        ])
        decorated = with_retry(max_retries=3, base_delay=0.01)(mock_func)

        result = await decorated()
        assert result == "success"
        assert mock_func.call_count == 3

    @pytest.mark.asyncio
    async def test_no_retry_on_non_retryable_error(self):
        """Should not retry on non-retryable error"""
        mock_func = AsyncMock(side_effect=NonRetryableError("Not found", status_code=404))
        decorated = with_retry(max_retries=3)(mock_func)

        with pytest.raises(NonRetryableError):
            await decorated()

        assert mock_func.call_count == 1

    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self):
        """Should raise error after max retries exceeded"""
        mock_func = AsyncMock(side_effect=RetryableError("Server error", status_code=500))
        decorated = with_retry(max_retries=3, base_delay=0.01)(mock_func)

        with pytest.raises(RetryableError):
            await decorated()

        assert mock_func.call_count == 4  # 1 initial + 3 retries


# ===================== Circuit Breaker Decorator Tests =====================

class TestWithCircuitBreaker:
    """Test circuit breaker decorator"""

    @pytest.mark.asyncio
    async def test_circuit_breaker_decorator_success(self):
        """Circuit breaker decorator should allow successful calls"""
        mock_func = AsyncMock(return_value="success")
        decorated = with_circuit_breaker(failure_threshold=3)(mock_func)

        result = await decorated()
        assert result == "success"

    @pytest.mark.asyncio
    async def test_circuit_breaker_opens_on_failures(self):
        """Circuit breaker should open after threshold failures"""
        mock_func = AsyncMock(side_effect=Exception("Error"))
        decorated = with_circuit_breaker(failure_threshold=2)(mock_func)

        # First two calls fail
        with pytest.raises(Exception):
            await decorated()
        with pytest.raises(Exception):
            await decorated()

        # Third call should be blocked
        with pytest.raises(Exception, match="Circuit breaker is OPEN"):
            await decorated()


# ===================== Fallback Strategy Tests =====================

class TestFallbackStrategy:
    """Test fallback strategy"""

    @pytest.mark.asyncio
    async def test_fallback_on_primary_failure(self):
        """Should fallback to backup when primary fails"""
        primary = AsyncMock(side_effect=Exception("Primary failed"))
        fallback = AsyncMock(return_value="fallback result")

        strategy = FallbackStrategy(primary, fallback)
        result = await strategy.execute()

        assert result == "fallback result"
        primary.assert_called_once()
        fallback.assert_called_once()

    @pytest.mark.asyncio
    async def test_no_fallback_on_success(self):
        """Should not use fallback when primary succeeds"""
        primary = AsyncMock(return_value="primary success")
        fallback = AsyncMock()

        strategy = FallbackStrategy(primary, fallback)
        result = await strategy.execute()

        assert result == "primary success"
        fallback.assert_not_called()

    @pytest.mark.asyncio
    async def test_multiple_fallbacks(self):
        """Should try multiple fallbacks in order"""
        primary = AsyncMock(side_effect=Exception("Primary failed"))
        fallback1 = AsyncMock(side_effect=Exception("Fallback1 failed"))
        fallback2 = AsyncMock(return_value="fallback2 success")

        strategy = FallbackStrategy(primary, fallback1, fallback2)
        result = await strategy.execute()

        assert result == "fallback2 success"

    @pytest.mark.asyncio
    async def test_all_fallbacks_fail(self):
        """Should raise error when all fallbacks fail"""
        primary = AsyncMock(side_effect=Exception("Primary failed"))
        fallback1 = AsyncMock(side_effect=Exception("Fallback1 failed"))

        strategy = FallbackStrategy(primary, fallback1)

        with pytest.raises(Exception, match="All strategies failed"):
            await strategy.execute()


# ===================== With Fallback Decorator Tests =====================

class TestWithFallback:
    """Test fallback decorator"""

    @pytest.mark.asyncio
    async def test_with_fallback_decorator(self):
        """Should use fallback when primary fails"""
        async def primary():
            raise Exception("Primary failed")

        async def fallback():
            return "fallback result"

        decorated = with_fallback(fallback)(primary)
        result = await decorated()

        assert result == "fallback result"


# ===================== Integration Tests =====================

class TestErrorHandlingIntegration:
    """Integration tests for error handling module"""

    @pytest.mark.asyncio
    async def test_retry_with_circuit_breaker(self):
        """Test retry combined with circuit breaker"""
        call_count = 0

        async def flaky_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise RetryableError("Temporary error", status_code=500)
            return "success"

        # Wrap with circuit breaker and retry
        cb = CircuitBreaker(failure_threshold=5)
        retry_config = RetryConfig(max_retries=3, base_delay=0.01)

        result = await with_retry(
            max_retries=retry_config.max_retries,
            base_delay=retry_config.base_delay
        )(with_circuit_breaker(cb)(flaky_function))()

        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_full_fallback_chain_with_retry(self):
        """Test fallback chain with retry mechanism"""
        call_count = {"primary": 0, "fallback": 0}

        async def primary():
            call_count["primary"] += 1
            if call_count["primary"] < 2:
                raise RetryableError("Primary failed", status_code=500)
            return "primary success"

        async def fallback():
            call_count["fallback"] += 1
            return "fallback success"

        # Primary with retry, then fallback
        try:
            result = await with_retry(max_retries=3, base_delay=0.01)(primary)()
        except Exception:
            result = await fallback()

        assert result == "primary success"


# ===================== Utility Function Tests =====================

class TestRetryWithBackoff:
    """Test retry_with_backoff utility function"""

    @pytest.mark.asyncio
    async def test_retry_with_backoff_success(self):
        """Test successful retry with backoff"""
        call_count = 0

        async def success_on_third():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Connection error")
            return "success"

        result = await retry_with_backoff(
            success_on_third,
            RetryConfig(max_retries=3, base_delay=0.01)
        )

        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_retry_with_backoff_all_fail(self):
        """Test retry with backoff when all attempts fail"""
        async def always_fails():
            raise ConnectionError("Always fails")

        with pytest.raises(ConnectionError):
            await retry_with_backoff(
                always_fails,
                RetryConfig(max_retries=2, base_delay=0.01)
            )

    @pytest.mark.asyncio
    async def test_retry_with_backoff_non_retryable(self):
        """Test retry with backoff doesn't retry non-retryable errors"""
        async def non_retryable_error():
            raise ValueError("Invalid input")

        with pytest.raises(ValueError):
            await retry_with_backoff(
                non_retryable_error,
                RetryConfig(max_retries=3, base_delay=0.01)
            )


class TestIsRetryableError:
    """Test is_retryable_error utility"""

    def test_retryable_error_returns_true(self):
        """Test RetryableError returns True"""
        error = RetryableError("Server error", status_code=500)
        assert is_retryable_error(error) is True

    def test_non_retryable_error_returns_false(self):
        """Test NonRetryableError returns False"""
        error = NonRetryableError("Not found", status_code=404)
        assert is_retryable_error(error) is False

    def test_connection_error_returns_true(self):
        """Test ConnectionError returns True"""
        error = ConnectionError("Connection refused")
        assert is_retryable_error(error) is True

    def test_timeout_error_returns_true(self):
        """Test TimeoutError returns True"""
        error = asyncio.TimeoutError("Timeout")
        assert is_retryable_error(error) is True

    def test_rate_limit_message_returns_true(self):
        """Test rate limit message returns True"""
        error = Exception("Rate limit exceeded (429)")
        assert is_retryable_error(error) is True

    def test_generic_error_returns_false(self):
        """Test generic error returns False by default"""
        error = ValueError("Invalid value")
        assert is_retryable_error(error) is False


# ===================== Additional Edge Case Tests =====================

class TestCircuitBreakerEdgeCases:
    """Additional circuit breaker edge case tests"""

    @pytest.mark.asyncio
    async def test_circuit_half_open_to_open_transition(self):
        """Circuit should reopen if failure occurs in half-open state"""
        cb = CircuitBreaker(
            failure_threshold=2,
            recovery_timeout=0.05,
            success_threshold=2
        )

        # Open the circuit
        await cb.record_failure()
        await cb.record_failure()
        assert cb.state == CircuitBreakerState.OPEN

        # Wait for recovery
        await asyncio.sleep(0.1)
        # Should transition to half-open
        assert cb.state == CircuitBreakerState.HALF_OPEN

        # Record failure in half-open - should reopen
        await cb.record_failure()
        assert cb.state == CircuitBreakerState.OPEN

    @pytest.mark.asyncio
    async def test_circuit_half_open_to_closed_transition(self):
        """Circuit should close after success_threshold in half-open"""
        cb = CircuitBreaker(
            failure_threshold=2,
            recovery_timeout=0.05,
            success_threshold=2
        )

        # Open the circuit
        await cb.record_failure()
        await cb.record_failure()
        assert cb.state == CircuitBreakerState.OPEN

        # Wait for recovery
        await asyncio.sleep(0.1)
        assert cb.state == CircuitBreakerState.HALF_OPEN

        # Record successes - should close
        await cb.record_success()
        await cb.record_success()
        assert cb.state == CircuitBreakerState.CLOSED


class TestRetryConfigJitter:
    """Test retry config with jitter"""

    def test_jitter_adds_randomness(self):
        """Test jitter adds randomness to delay calculation"""
        config = RetryConfig(base_delay=1.0, exponential_base=2, jitter=True)

        delays = set()
        for _ in range(100):
            delay = config.calculate_delay(0)
            delays.add(int(delay * 100))  # Convert to integer for comparison

        # With jitter, delays should vary
        assert len(delays) > 1

    def test_no_jitter_is_deterministic(self):
        """Test no jitter gives deterministic results"""
        config = RetryConfig(base_delay=1.0, exponential_base=2, jitter=False)

        delays = [config.calculate_delay(0) for _ in range(10)]

        # Without jitter, all delays should be the same
        assert len(set(delays)) == 1
        assert delays[0] == 1.0