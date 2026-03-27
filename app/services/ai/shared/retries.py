"""Shared tenacity retry policy for all AI service calls.

Import `llm_retry` and apply it as a decorator instead of redefining the
policy in each service.  Change the policy here once; every service picks it up.
"""

from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

llm_retry = retry(
    retry=retry_if_exception_type((TimeoutError, ConnectionError)),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    reraise=True,
)
