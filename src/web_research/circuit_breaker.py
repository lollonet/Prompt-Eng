"""
Enterprise Circuit Breaker implementation with exponential backoff and health monitoring.
"""

import asyncio
import logging
import statistics
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, Optional, TypeVar, Union

from .config import CircuitBreakerConfig
from .interfaces import ICircuitBreaker

T = TypeVar("T")


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Blocking requests
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitMetrics:
    """Metrics for circuit breaker monitoring."""

    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    last_failure_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    response_times: list = field(default_factory=list)

    @property
    def failure_rate(self) -> float:
        """Calculate failure rate."""
        if self.total_requests == 0:
            return 0.0
        return self.failed_requests / self.total_requests

    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        return 1.0 - self.failure_rate

    @property
    def average_response_time(self) -> float:
        """Calculate average response time."""
        if not self.response_times:
            return 0.0
        return statistics.mean(self.response_times[-100:])  # Last 100 requests


class CircuitBreakerException(Exception):
    """Raised when circuit breaker is open."""

    pass


class CircuitBreaker(ICircuitBreaker):
    """
    Enterprise circuit breaker with:
    - Exponential backoff
    - Health monitoring
    - Configurable failure thresholds
    - Metrics collection
    - Async support
    """

    def __init__(
        self, name: str, config: CircuitBreakerConfig, logger: Optional[logging.Logger] = None
    ):
        self.name = name
        self.config = config
        self._logger = logger or logging.getLogger(f"{__name__}.{name}")

        # State management
        self._state = CircuitState.CLOSED
        self._last_failure_time: Optional[float] = None
        self._timeout_start_time: Optional[float] = None
        self._current_timeout = config.timeout_seconds

        # Metrics
        self._metrics = CircuitMetrics()

        # Thread safety
        self._lock = asyncio.Lock()

        # Health check callback
        self._health_check: Optional[Callable] = None

        self._logger.info(f"Circuit breaker '{name}' initialized with config: {config}")

    async def call(self, func: Callable[..., T], *args, **kwargs) -> T:
        """Execute function with circuit breaker protection."""
        async with self._lock:
            # Check if circuit should remain open
            await self._update_state()

            if self._state == CircuitState.OPEN:
                self._logger.warning(f"Circuit breaker '{self.name}' is OPEN - request blocked")
                raise CircuitBreakerException(
                    f"Circuit breaker '{self.name}' is open. "
                    f"Next retry in {self._get_remaining_timeout():.1f}s"
                )

        # Execute the function
        start_time = time.time()
        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)

            # Record success
            response_time = time.time() - start_time
            await self._record_success(response_time)

            return result

        except Exception as e:
            # Record failure
            response_time = time.time() - start_time
            await self._record_failure(response_time, e)
            raise

    async def _update_state(self) -> None:
        """Update circuit breaker state based on current conditions."""
        current_time = time.time()

        if self._state == CircuitState.OPEN:
            # Check if timeout has expired
            if (
                self._timeout_start_time
                and current_time - self._timeout_start_time >= self._current_timeout
            ):

                self._logger.info(f"Circuit breaker '{self.name}' transitioning to HALF_OPEN")
                self._state = CircuitState.HALF_OPEN
                self._timeout_start_time = None

        elif self._state == CircuitState.HALF_OPEN:
            # Check if we should close or re-open
            if self._metrics.consecutive_successes >= self.config.success_threshold:
                await self._close_circuit()
            elif self._metrics.consecutive_failures > 0:
                await self._open_circuit()

        elif self._state == CircuitState.CLOSED:
            # Check if we should open due to failures
            if self._metrics.consecutive_failures >= self.config.failure_threshold or (
                self._metrics.total_requests >= 10 and self._metrics.failure_rate > 0.5
            ):
                await self._open_circuit()

    async def _record_success(self, response_time: float) -> None:
        """Record successful execution."""
        async with self._lock:
            self._metrics.total_requests += 1
            self._metrics.successful_requests += 1
            self._metrics.consecutive_successes += 1
            self._metrics.consecutive_failures = 0
            self._metrics.last_success_time = datetime.now()
            self._metrics.response_times.append(response_time)

            # Keep only recent response times
            if len(self._metrics.response_times) > 1000:
                self._metrics.response_times = self._metrics.response_times[-500:]

        self._logger.debug(
            f"Circuit breaker '{self.name}' - Success recorded "
            f"(response_time: {response_time:.3f}s, consecutive: {self._metrics.consecutive_successes})"
        )

        # If we're in HALF_OPEN and have enough successes, close the circuit
        if (
            self._state == CircuitState.HALF_OPEN
            and self._metrics.consecutive_successes >= self.config.success_threshold
        ):
            await self._close_circuit()

    async def _record_failure(self, response_time: float, exception: Exception) -> None:
        """Record failed execution."""
        async with self._lock:
            self._metrics.total_requests += 1
            self._metrics.failed_requests += 1
            self._metrics.consecutive_failures += 1
            self._metrics.consecutive_successes = 0
            self._metrics.last_failure_time = datetime.now()
            self._metrics.response_times.append(response_time)

        self._logger.warning(
            f"Circuit breaker '{self.name}' - Failure recorded "
            f"(response_time: {response_time:.3f}s, consecutive: {self._metrics.consecutive_failures}, "
            f"error: {type(exception).__name__}: {str(exception)[:100]})"
        )

        # Check if we should open the circuit
        if (
            self._state == CircuitState.CLOSED
            and self._metrics.consecutive_failures >= self.config.failure_threshold
        ):
            await self._open_circuit()
        elif self._state == CircuitState.HALF_OPEN:
            await self._open_circuit()

    async def _open_circuit(self) -> None:
        """Open the circuit breaker."""
        self._state = CircuitState.OPEN
        self._timeout_start_time = time.time()

        # Apply exponential backoff
        if self.config.exponential_backoff:
            self._current_timeout = min(self._current_timeout * 2, self.config.max_timeout_seconds)

        self._logger.error(
            f"Circuit breaker '{self.name}' OPENED - "
            f"consecutive failures: {self._metrics.consecutive_failures}, "
            f"timeout: {self._current_timeout}s"
        )

    async def _close_circuit(self) -> None:
        """Close the circuit breaker."""
        self._state = CircuitState.CLOSED
        self._current_timeout = self.config.timeout_seconds
        self._timeout_start_time = None

        self._logger.info(
            f"Circuit breaker '{self.name}' CLOSED - "
            f"consecutive successes: {self._metrics.consecutive_successes}"
        )

    def _get_remaining_timeout(self) -> float:
        """Get remaining timeout duration."""
        if not self._timeout_start_time:
            return 0.0

        elapsed = time.time() - self._timeout_start_time
        return max(0.0, self._current_timeout - elapsed)

    def is_open(self) -> bool:
        """Check if circuit is open."""
        return self._state == CircuitState.OPEN

    def is_half_open(self) -> bool:
        """Check if circuit is half-open."""
        return self._state == CircuitState.HALF_OPEN

    def is_closed(self) -> bool:
        """Check if circuit is closed."""
        return self._state == CircuitState.CLOSED

    async def reset(self) -> None:
        """Reset circuit breaker to closed state."""
        async with self._lock:
            self._state = CircuitState.CLOSED
            self._current_timeout = self.config.timeout_seconds
            self._timeout_start_time = None
            self._metrics = CircuitMetrics()

        self._logger.info(f"Circuit breaker '{self.name}' reset to CLOSED state")

    def get_metrics(self) -> CircuitMetrics:
        """Get current metrics."""
        return self._metrics

    def get_state(self) -> CircuitState:
        """Get current state."""
        return self._state

    def set_health_check(self, health_check: Callable[[], bool]) -> None:
        """Set health check function."""
        self._health_check = health_check

    async def health_check(self) -> bool:
        """Perform health check."""
        if not self._health_check:
            return True

        try:
            if asyncio.iscoroutinefunction(self._health_check):
                return await self._health_check()
            else:
                return self._health_check()
        except Exception as e:
            self._logger.error(f"Health check failed for '{self.name}': {e}")
            return False

    def __str__(self) -> str:
        """String representation."""
        return (
            f"CircuitBreaker(name='{self.name}', state={self._state.value}, "
            f"failures={self._metrics.consecutive_failures}, "
            f"successes={self._metrics.consecutive_successes})"
        )


class CircuitBreakerManager:
    """Manages multiple circuit breakers."""

    def __init__(self, default_config: CircuitBreakerConfig):
        self.default_config = default_config
        self._breakers: Dict[str, CircuitBreaker] = {}
        self._logger = logging.getLogger(__name__)

    def get_breaker(
        self, name: str, config: Optional[CircuitBreakerConfig] = None
    ) -> CircuitBreaker:
        """Get or create circuit breaker."""
        if name not in self._breakers:
            breaker_config = config or self.default_config
            self._breakers[name] = CircuitBreaker(name, breaker_config, self._logger)

        return self._breakers[name]

    async def reset_all(self) -> None:
        """Reset all circuit breakers."""
        for breaker in self._breakers.values():
            await breaker.reset()

        self._logger.info("All circuit breakers reset")

    async def health_check_all(self) -> Dict[str, bool]:
        """Perform health check on all breakers."""
        results = {}
        for name, breaker in self._breakers.items():
            results[name] = await breaker.health_check()

        return results

    def get_all_metrics(self) -> Dict[str, CircuitMetrics]:
        """Get metrics for all breakers."""
        return {name: breaker.get_metrics() for name, breaker in self._breakers.items()}

    @asynccontextmanager
    async def protected_call(self, breaker_name: str, func: Callable, *args, **kwargs):
        """Context manager for protected function calls."""
        breaker = self.get_breaker(breaker_name)
        try:
            result = await breaker.call(func, *args, **kwargs)
            yield result
        except CircuitBreakerException:
            self._logger.warning(f"Circuit breaker '{breaker_name}' blocked request")
            raise
        except Exception as e:
            self._logger.error(f"Protected call failed for '{breaker_name}': {e}")
            raise
