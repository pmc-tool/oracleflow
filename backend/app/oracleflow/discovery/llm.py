"""Sync LLM client for OracleFlow discovery and entity modules."""

from __future__ import annotations

import logging

import requests

from app.config import Config
from app.oracleflow.exceptions import ClassificationError

logger = logging.getLogger(__name__)


class LLMClient:
    """Sends chat-completion requests to the configured LLM endpoint (sync)."""

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        api_key: str | None = None,
        timeout: float = 120.0,
    ) -> None:
        self.base_url = (base_url or Config.LLM_BASE_URL).rstrip("/")
        self.model = model or Config.LLM_MODEL_NAME
        self.api_key = api_key or Config.LLM_API_KEY
        self.timeout = timeout

    def classify(self, system_prompt: str, content: str) -> str:
        """Send a chat completion request and return the assistant message content.

        :param system_prompt: The system-level instruction.
        :param content: The user-level content (e.g. page text to classify).
        :returns: The raw assistant response text.
        :raises ClassificationError: On network or API errors.
        """
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": content},
            ],
            "temperature": 0.1,
        }
        headers = {
            "Content-Type": "application/json",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        try:
            resp = requests.post(
                url, json=payload, headers=headers, timeout=self.timeout
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
        except requests.HTTPError as exc:
            logger.error(
                "LLM API returned %s: %s",
                exc.response.status_code if exc.response else "?",
                exc.response.text if exc.response else str(exc),
            )
            raise ClassificationError(
                f"LLM API error: {exc}"
            ) from exc
        except (requests.RequestException, KeyError, IndexError) as exc:
            logger.error("LLM request failed: %s", exc)
            raise ClassificationError(f"LLM request failed: {exc}") from exc
