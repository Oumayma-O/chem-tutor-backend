"""Shared tenacity retry policy for all AI service calls.

Import `llm_retry` and apply it as a decorator instead of redefining the
policy in each service.  Change the policy here once; every service picks it up.
"""

from __future__ import annotations

from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

# HTTP status codes where a quick retry often succeeds (timeouts, overload, rate limits).
_RETRIABLE_OPENAI_STATUS = frozenset({408, 429, 500, 502, 503, 504})


def _transient_llm_error(exc: BaseException) -> bool:
    if isinstance(exc, (TimeoutError, ConnectionError)):
        return True
    try:
        import httpx

        if isinstance(
            exc,
            (
                httpx.ConnectError,
                httpx.ReadTimeout,
                httpx.WriteTimeout,
                httpx.ConnectTimeout,
                httpx.RemoteProtocolError,
                httpx.PoolTimeout,
            ),
        ):
            return True
    except ImportError:
        pass
    try:
        from openai import APIConnectionError, APITimeoutError, InternalServerError, RateLimitError
        from openai import APIStatusError

        if isinstance(exc, (APIConnectionError, APITimeoutError, InternalServerError, RateLimitError)):
            return True
        if isinstance(exc, APIStatusError):
            code = getattr(exc, "status_code", None)
            return code in _RETRIABLE_OPENAI_STATUS
    except ImportError:
        pass
    try:
        from anthropic import APIConnectionError as AnthropicAPIConnectionError
        from anthropic import RateLimitError as AnthropicRateLimitError

        if isinstance(exc, (AnthropicAPIConnectionError, AnthropicRateLimitError)):
            return True
    except ImportError:
        pass
    return False


llm_retry = retry(
    retry=retry_if_exception(_transient_llm_error),
    stop=stop_after_attempt(4),
    wait=wait_exponential(multiplier=1, min=1, max=20),
    reraise=True,
)
