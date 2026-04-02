"""Retry and rate limiting utilities with conservative backoff strategy."""

import asyncio
import random
import time
from functools import wraps
from typing import Callable, TypeVar, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from aiohttp import ClientConnectorError

import structlog
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

from .config import get_config

logger = structlog.get_logger(__name__)
config = get_config()


class RateLimiter:
    """Simple async rate limiter for conservative request pacing."""
    
    def __init__(self, rate: float = 1.0):
        self.update_rate(rate)
        self.last_call = 0.0
        
    def update_rate(self, rate: float):
        self.rate = rate  # requests per second
        self.min_interval = 1.0 / rate if rate > 0 else 1.0
    
    async def acquire(self):
        """Wait until we can make another request."""
        now = time.time()
        time_since_last = now - self.last_call
        
        if time_since_last < self.min_interval:
            await asyncio.sleep(self.min_interval - time_since_last + random.uniform(0.05, 0.15))
        
        self.last_call = time.time()


# Global rate limiters per region
_rate_limiters: dict = {}


def get_rate_limiter(region: str = "default", concurrency_multiplier: int = 1) -> RateLimiter:
    """Get or create rate limiter for a region."""
    rps = config.rate_limit.get("requests_per_second_per_worker", 0.8) * concurrency_multiplier
    if region not in _rate_limiters:
        _rate_limiters[region] = RateLimiter(rate=rps)
    else:
        _rate_limiters[region].update_rate(rps)
    return _rate_limiters[region]


def with_retry(func: Callable):
    """Decorator for conservative retry strategy."""
    
    @wraps(func)
    async def wrapper(*args, **kwargs):
        max_retries = config.rate_limit.get("max_retries", 6)
        backoff_factor = config.rate_limit.get("backoff_factor", 2.0)
        
        attempt = 0
        last_exception = None
        
        while attempt < max_retries:
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                attempt += 1
                
                error_msg = str(e).lower()
                status_code = getattr(e, "status", None) or getattr(e, "status_code", None)
                
                # Special handling for Steam rate limits and errors
                is_connector_error = False
                try:
                    from aiohttp import ClientConnectorError
                    is_connector_error = isinstance(e, ClientConnectorError)
                except ImportError:
                    pass
                
                if status_code == 429 or "rate limit" in error_msg or "too many requests" in error_msg or is_connector_error:
                    wait_time = min(2 ** attempt * 3, 45) + random.uniform(1, 5)
                    logger.warning(f"Rate limited (429). Waiting {wait_time:.1f}s", 
                                 attempt=attempt, region=kwargs.get("cc"))
                    await asyncio.sleep(wait_time)
                    continue
                    
                elif status_code in (503, 504, 502) or "service unavailable" in error_msg:
                    wait_time = min(2 ** attempt * 2, 30)
                    logger.warning(f"Service error {status_code}. Backing off {wait_time:.1f}s")
                    await asyncio.sleep(wait_time)
                    continue
                    
                elif status_code in (403, 401):
                    logger.error("Access forbidden. Check network or if IP is blocked.", 
                               status_code=status_code)
                    raise
                
                # General retry with jitter
                if attempt < max_retries - 1:
                    jitter = random.uniform(0.1, 0.4)
                    wait_time = (backoff_factor ** attempt) * (1 + jitter)
                    wait_time = min(wait_time, 25.0)
                    
                    logger.warning(f"Request failed, retrying in {wait_time:.1f}s", 
                                 error=type(e).__name__, attempt=attempt, max_retries=max_retries)
                    await asyncio.sleep(wait_time)
                else:
                    logger.error("Request failed after max retries", 
                               error=type(e).__name__, last_error=str(e))
                    raise
        
        if last_exception:
            raise last_exception
    
    return wrapper


async def adaptive_sleep(error_count: int = 0, base_delay: float = 1.0):
    """Adaptive sleep based on recent error rate."""
    if error_count == 0:
        await asyncio.sleep(base_delay)
        return
    
    # Increase delay as error rate increases
    multiplier = 1 + (error_count * 0.6)
    delay = min(base_delay * multiplier, 8.0)
    jitter = random.uniform(-0.2, 0.3)
    
    await asyncio.sleep(max(delay + jitter, 0.5))
    logger.debug("Adaptive sleep applied", delay=delay, error_count=error_count)
