import time
import logging

logger = logging.getLogger(__name__)

def retry_llm_call(fn, max_retries=3, base_delay=2):
    """Retry an LLM API call with exponential backoff."""
    for attempt in range(max_retries):
        try:
            return fn()
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            delay = base_delay * (2 ** attempt)
            logger.warning(f"LLM call failed (attempt {attempt+1}/{max_retries}): {e}. Retrying in {delay}s...")
            time.sleep(delay)
