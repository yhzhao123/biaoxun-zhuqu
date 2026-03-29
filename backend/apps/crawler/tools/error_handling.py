"""
Error Handling Module for Deer-Flow Tools

Provides:
1. Error classification (network errors, timeouts, API limits)
2. Smart retry mechanism (exponential backoff, max retries)
3. Circuit breaker pattern
4. Fallback strategy (switch to backup when primary fails)
"""
import asyncio
import logging
import random
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps
from typing import Any, Awaitable, Callable, Dict, List, Optional, TypeVar, Union

logger = logging.getLogger(__name__)

T = TypeVar('T')


# ===================== Error Category =====================

class ErrorCategory(Enum):
    """Error category classification"""
    NETWORK = "network"        # Network connectivity issues
    TIMEOUT = "timeout"        # Request timeout
    RATE_LIMIT = "rate_limit"  # HTTP 429
    SERVER_ERROR = "server_error"  # HTTP 5xx
    CLIENT_ERROR = "client_error"  # HTTP 4xx (except 429)
    UNKNOWN = "unknown"        # Unknown error


# ===================== Custom Error Classes =====================

class RetryableError(Exception):
    """Error that can be retried"""

    def __init__(self, message: str, status_code: Optional[int] = None):
        self.message = message
        self.status_code = status_code
        super().__init__(message)

    def is_retryable(self) -> bool:
        """Check if error is retryable"""
        if self.status_code:
            # Retry on rate limit (429) or server errors (5xx)
            if self.status_code == 429 or 500 <= self.status_code < 600:
                return True
        return True  # Default to retryable


class NonRetryableError(Exception):
    """Error that should not be retried"""

    def __init__(self, message: str, status_code: Optional[int] = None):
        self.message = message
        self.status_code = status_code
        super().__init__(message)

    def is_retryable(self) -> bool:
        """Check if error is retryable"""
        return False


# ===================== Error Classification =====================

class ErrorClassifier:
    """Classify errors into categories"""

    @staticmethod
    def classify(error: Exception) -> ErrorCategory:
        """
        Classify error into category

        Args:
            error: Exception to classify

        Returns:
            ErrorCategory: The category of the error
        """
        error_message = str(error).lower()
        error_type = type(error).__name__

        # Check for specific error types
        if isinstance(error, RetryableError):
            if error.status_code == 429:
                return ErrorCategory.RATE_LIMIT
            if error.status_code and 500 <= error.status_code < 600:
                return ErrorCategory.SERVER_ERROR
            # For custom RetryableError without status code
            if "timeout" in error_message or "timed out" in error_message:
                return ErrorCategory.TIMEOUT
            if "connection" in error_message or "network" in error_message:
                return ErrorCategory.NETWORK
            return ErrorCategory.SERVER_ERROR

        if isinstance(error, NonRetryableError):
            if error.status_code and 400 <= error.status_code < 500:
                return ErrorCategory.CLIENT_ERROR
            return ErrorCategory.UNKNOWN

        # Check by error type
        if error_type in ("ConnectionError", "ConnectionRefusedError",
                          "ConnectionResetError", "OSError"):
            return ErrorCategory.NETWORK

        if error_type in ("TimeoutError", "asyncio.TimeoutError",
                          "httpx.TimeoutException", "requests.Timeout"):
            return ErrorCategory.TIMEOUT

        # Check by error message
        if "429" in error_message or "rate limit" in error_message:
            return ErrorCategory.RATE_LIMIT

        if "500" in error_message or "502" in error_message or "503" in error_message:
            return ErrorCategory.SERVER_ERROR

        if "404" in error_message or "400" in error_message or "401" in error_message:
            return ErrorCategory.CLIENT_ERROR

        return ErrorCategory.UNKNOWN


# Update ErrorCategory to have classify method
ErrorCategory.classify = ErrorClassifier.classify


# ===================== Retry Configuration =====================

@dataclass
class RetryConfig:
    """Configuration for retry behavior"""

    max_retries: int = 3
    base_delay: float = 1.0  # Base delay in seconds
    max_delay: float = 60.0  # Maximum delay in seconds
    exponential_base: float = 2.0  # Base for exponential backoff
    jitter: bool = True  # Add randomness to delay

    def calculate_delay(self, attempt: int) -> float:
        """
        Calculate delay for given attempt number

        Args:
            attempt: Current attempt number (0-indexed)

        Returns:
            float: Delay in seconds
        """
        # Exponential backoff: base_delay * (exponential_base ^ attempt)
        delay = self.base_delay * (self.exponential_base ** attempt)

        # Cap at max_delay
        delay = min(delay, self.max_delay)

        # Add jitter
        if self.jitter:
            delay = delay * (0.5 + random.random())  # 0.5 to 1.5

        return delay


# ===================== Circuit Breaker =====================

class CircuitBreakerState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreaker:
    """
    Circuit breaker pattern implementation

    Prevents cascading failures by stopping requests to a failing service
    """

    failure_threshold: int = 5  # Number of failures to open circuit
    recovery_timeout: float = 60.0  # Seconds before attempting recovery
    success_threshold: int = 2  # Successes needed to close circuit

    _state: CircuitBreakerState = field(default=CircuitBreakerState.CLOSED, init=False)
    _failure_count: int = field(default=0, init=False)
    _success_count: int = field(default=0, init=False)
    _last_failure_time: float = field(default=0.0, init=False)

    @property
    def state(self) -> CircuitBreakerState:
        """Get current circuit breaker state"""
        if self._state == CircuitBreakerState.OPEN:
            # Check if recovery timeout has passed
            import time
            if time.time() - self._last_failure_time >= self.recovery_timeout:
                self._state = CircuitBreakerState.HALF_OPEN
        return self._state

    async def can_execute(self) -> bool:
        """Check if execution is allowed"""
        state = self.state
        return state in (CircuitBreakerState.CLOSED, CircuitBreakerState.HALF_OPEN)

    async def record_success(self):
        """Record a successful execution"""
        if self._state == CircuitBreakerState.HALF_OPEN:
            self._success_count += 1
            if self._success_count >= self.success_threshold:
                self._state = CircuitBreakerState.CLOSED
                self._failure_count = 0
                self._success_count = 0
                logger.info("Circuit breaker closed")
        elif self._state == CircuitBreakerState.CLOSED:
            # Reset failure count on success
            self._failure_count = 0

    async def record_failure(self):
        """Record a failed execution"""
        import time

        # If circuit is already open, don't record more failures
        if self._state == CircuitBreakerState.OPEN:
            raise Exception(
                f"Circuit breaker is OPEN. Service temporarily unavailable."
            )

        self._failure_count += 1
        self._last_failure_time = time.time()

        if self._state == CircuitBreakerState.HALF_OPEN:
            # Any failure in half-open state opens the circuit again
            self._state = CircuitBreakerState.OPEN
            self._success_count = 0
            logger.warning("Circuit breaker reopened after failure in half-open state")
        elif self._state == CircuitBreakerState.CLOSED:
            if self._failure_count >= self.failure_threshold:
                self._state = CircuitBreakerState.OPEN
                logger.warning(f"Circuit breaker opened after {self._failure_count} failures")


# ===================== Retry Decorator =====================

def with_retry(
    max_retries: Optional[int] = None,
    base_delay: Optional[float] = None,
    max_delay: Optional[float] = None,
    exponential_base: Optional[float] = None,
    jitter: Optional[bool] = None,
    retryable_exceptions: Optional[List[type]] = None,
) -> Callable:
    """
    Decorator to add retry logic to async functions

    Args:
        max_retries: Maximum number of retries (default: 3)
        base_delay: Base delay in seconds (default: 1.0)
        max_delay: Maximum delay in seconds (default: 60.0)
        exponential_base: Base for exponential backoff (default: 2.0)
        jitter: Add randomness to delay (default: True)
        retryable_exceptions: List of exception types to retry (default: all)

    Returns:
        Decorated function with retry logic
    """
    config = RetryConfig(
        max_retries=max_retries or 3,
        base_delay=base_delay or 1.0,
        max_delay=max_delay or 60.0,
        exponential_base=exponential_base or 2.0,
        jitter=jitter if jitter is not None else True,
    )

    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            last_exception = None

            for attempt in range(config.max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e

                    # Check if exception is retryable
                    is_retryable = False
                    if retryable_exceptions:
                        is_retryable = any(isinstance(e, exc_type)
                                          for exc_type in retryable_exceptions)
                    elif isinstance(e, RetryableError):
                        is_retryable = e.is_retryable()
                    elif isinstance(e, (ConnectionError, asyncio.TimeoutError)):
                        is_retryable = True

                    # Don't retry if not retryable or out of retries
                    if not is_retryable or attempt >= config.max_retries:
                        raise

                    # Calculate delay
                    delay = config.calculate_delay(attempt)
                    logger.warning(
                        f"Retry {attempt + 1}/{config.max_retries} for {func.__name__}: "
                        f"{type(e).__name__}: {e}. Waiting {delay:.2f}s"
                    )
                    await asyncio.sleep(delay)

            # Should not reach here, but just in case
            if last_exception:
                raise last_exception
            raise RuntimeError("Retry logic failed unexpectedly")

        return wrapper
    return decorator


# ===================== Circuit Breaker Decorator =====================

def with_circuit_breaker(
    circuit_breaker: Optional[CircuitBreaker] = None,
    failure_threshold: int = 5,
    recovery_timeout: float = 60.0,
    success_threshold: int = 2,
) -> Callable:
    """
    Decorator to add circuit breaker to async functions

    Args:
        circuit_breaker: Existing CircuitBreaker instance
        failure_threshold: Number of failures to open circuit
        recovery_timeout: Seconds before attempting recovery
        success_threshold: Successes needed to close circuit

    Returns:
        Decorated function with circuit breaker
    """
    if circuit_breaker is None:
        circuit_breaker = CircuitBreaker(
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            success_threshold=success_threshold,
        )

    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            # Check if circuit allows execution
            if not await circuit_breaker.can_execute():
                raise Exception(
                    f"Circuit breaker is OPEN for {func.__name__}. "
                    "Service temporarily unavailable."
                )

            try:
                result = await func(*args, **kwargs)
                await circuit_breaker.record_success()
                return result
            except Exception as e:
                await circuit_breaker.record_failure()
                raise

        # Expose circuit breaker for external access
        wrapper.circuit_breaker = circuit_breaker
        return wrapper
    return decorator


# ===================== Fallback Strategy =====================

class FallbackStrategy:
    """
    Fallback strategy that tries multiple functions in order

    When primary fails, tries fallback functions in sequence
    """

    def __init__(
        self,
        primary: Callable[..., Awaitable[T]],
        *fallbacks: Callable[..., Awaitable[T]]
    ):
        self.primary = primary
        self.fallbacks = fallbacks

    async def execute(self, *args, **kwargs) -> T:
        """
        Execute strategy, trying each function in order

        Args:
            *args: Positional arguments to pass to functions
            **kwargs: Keyword arguments to pass to functions

        Returns:
            Result from first successful function

        Raises:
            Exception: If all strategies fail
        """
        errors = []

        # Try primary
        try:
            return await self.primary(*args, **kwargs)
        except Exception as e:
            errors.append((self.primary.__name__, e))
            logger.warning(f"Primary strategy failed: {e}")

        # Try fallbacks in order
        for i, fallback in enumerate(self.fallbacks):
            try:
                result = await fallback(*args, **kwargs)
                logger.info(f"Fallback {i + 1} succeeded: {fallback.__name__}")
                return result
            except Exception as e:
                errors.append((fallback.__name__, e))
                logger.warning(f"Fallback {i + 1} failed: {e}")

        # All strategies failed
        error_messages = "; ".join(f"{name}: {err}" for name, err in errors)
        raise Exception(f"All strategies failed: {error_messages}")


def with_fallback(
    fallback: Callable[..., Awaitable[T]],
    *more_fallbacks: Callable[..., Awaitable[T]]
) -> Callable:
    """
    Decorator to add fallback logic to async functions

    Args:
        fallback: Fallback function to call when primary fails
        *more_fallbacks: Additional fallback functions

    Returns:
        Decorated function with fallback logic
    """
    def decorator(
        func: Callable[..., Awaitable[T]]
    ) -> Callable[..., Awaitable[T]]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            strategy = FallbackStrategy(func, fallback, *more_fallbacks)
            return await strategy.execute(*args, **kwargs)
        return wrapper
    return decorator


# ===================== Utility Functions =====================

async def retry_with_backoff(
    func: Callable[..., Awaitable[T]],
    config: Optional[RetryConfig] = None,
    *args,
    **kwargs
) -> T:
    """
    Retry a function with exponential backoff

    Args:
        func: Async function to retry
        config: Retry configuration
        *args: Positional arguments for func
        **kwargs: Keyword arguments for func

    Returns:
        Result from successful execution
    """
    if config is None:
        config = RetryConfig()

    last_exception = None
    for attempt in range(config.max_retries + 1):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            last_exception = e

            # Check if should retry
            if not isinstance(e, (RetryableError, ConnectionError, asyncio.TimeoutError)):
                raise

            if attempt >= config.max_retries:
                raise

            delay = config.calculate_delay(attempt)
            logger.warning(f"Retry {attempt + 1}/{config.max_retries}: {e}. Waiting {delay:.2f}s")
            await asyncio.sleep(delay)

    raise last_exception


def is_retryable_error(error: Exception) -> bool:
    """
    Check if an error is retryable

    Args:
        error: Exception to check

    Returns:
        bool: True if error should be retried
    """
    # Check custom error types
    if isinstance(error, RetryableError):
        return error.is_retryable()
    if isinstance(error, NonRetryableError):
        return False

    # Check common retryable error types
    retryable_types = (
        ConnectionError,
        asyncio.TimeoutError,
        TimeoutError,
    )

    if isinstance(error, retryable_types):
        return True

    # Check for common retryable status codes in error messages
    error_str = str(error).lower()
    if "429" in error_str or "rate limit" in error_str:
        return True

    return False