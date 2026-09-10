"""
OpenRouter API Client with proper attribution headers for analytics.
"""

import json
import logging
import time
from dataclasses import dataclass
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


@dataclass
class OpenRouterConfig:
    """Configuration for OpenRouter API client."""

    api_key: str
    model: str = "openai/gpt-4o-mini"
    temperature: float = 0.7
    max_tokens: int = 2048
    site_url: str = "https://github.com/zysec-ai/data4ai"
    site_name: str = "Data4AI"
    timeout: int = 30


class OpenRouterClient:
    """OpenRouter API client with proper attribution headers and rate limiting."""

    BASE_URL = "https://openrouter.ai/api/v1"

    def __init__(self, config: OpenRouterConfig):
        self.config = config
        self.client = httpx.AsyncClient(timeout=config.timeout)

        # Initialize rate limiter
        from data4ai.rate_limiter import (
            AdaptiveRateLimiter,
            RateLimitConfig,
            RequestMetrics,
        )

        rate_config = RateLimitConfig(
            requests_per_minute=60,  # Default, can be overridden
            max_concurrent=10,
        )
        self.rate_limiter = AdaptiveRateLimiter(rate_config)
        self.metrics = RequestMetrics()

    def _get_headers(self) -> dict[str, str]:
        """Get headers with proper attribution for analytics."""
        return {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": self.config.site_url,
            "X-Title": self.config.site_name,
        }

    def _get_payload(self, messages: list[dict[str, str]], **kwargs) -> dict[str, Any]:
        """Build the request payload."""
        return {
            "model": kwargs.get("model", self.config.model),
            "messages": messages,
            "temperature": kwargs.get("temperature", self.config.temperature),
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
            "stream": False,
        }

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def chat_completion(
        self, messages: list[dict[str, str]], **kwargs
    ) -> dict[str, Any]:
        """
        Make a chat completion request to OpenRouter with proper attribution.

        Args:
            messages: List of message dictionaries with 'role' and 'content'
            **kwargs: Additional parameters (model, temperature, max_tokens)

        Returns:
            API response dictionary

        Raises:
            httpx.HTTPError: If the request fails
        """
        url = f"{self.BASE_URL}/chat/completions"
        headers = self._get_headers()
        payload = self._get_payload(messages, **kwargs)

        logger.info(f"Making OpenRouter API call to {url}")
        logger.debug(f"Headers: {headers}")
        logger.debug(f"Payload: {json.dumps(payload, indent=2)}")

        # Use rate limiter context manager
        async with self.rate_limiter:
            start_time = time.time()

            try:
                response = await self.client.post(
                    url=url, headers=headers, json=payload
                )
                response.raise_for_status()

                result = response.json()
                latency = time.time() - start_time

                logger.info(
                    f"OpenRouter API call successful. Model: {payload['model']}"
                )

                # Record metrics
                tokens_used = 0
                if "usage" in result:
                    usage = result["usage"]
                    tokens_used = usage.get("total_tokens", 0)
                    logger.info(f"Tokens used: {tokens_used}")

                self.metrics.record_request(True, latency, tokens_used)

                return result

            except httpx.HTTPError as e:
                latency = time.time() - start_time
                self.metrics.record_request(False, latency)

                # Handle rate limiting specifically
                if (
                    hasattr(e, "response")
                    and e.response
                    and e.response.status_code == 429
                ):
                    retry_after = e.response.headers.get("Retry-After")
                    await self.rate_limiter.handle_429(
                        int(retry_after) if retry_after else None
                    )

                logger.error(f"OpenRouter API call failed: {e}")
                logger.error(
                    f"Response: {e.response.text if hasattr(e, 'response') and e.response else 'No response'}"
                )
                raise

    async def list_models(self) -> list[dict[str, Any]]:
        """List available models from OpenRouter."""
        url = f"{self.BASE_URL}/models"
        headers = self._get_headers()

        async with self.rate_limiter:
            try:
                response = await self.client.get(url=url, headers=headers)
                response.raise_for_status()
                return response.json()["data"]
            except httpx.HTTPError as e:
                logger.error(f"Failed to list models: {e}")
                raise

    async def validate_model(self, model: str) -> bool:
        """Validate if a model is available."""
        try:
            models = await self.list_models()
            available_models = [m["id"] for m in models]
            return model in available_models
        except Exception:
            return False

    def get_metrics(self) -> dict[str, Any]:
        """Get current API metrics."""
        return self.metrics.get_metrics()

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


# Synchronous wrapper for convenience
class SyncOpenRouterClient:
    """Synchronous wrapper for OpenRouter client."""

    BASE_URL = "https://openrouter.ai/api/v1"

    def __init__(self, config: OpenRouterConfig):
        self.config = config
        self.client = httpx.Client(timeout=config.timeout)

        # Initialize metrics for sync client
        from data4ai.rate_limiter import RequestMetrics

        self.metrics = RequestMetrics()

    def _get_headers(self) -> dict[str, str]:
        """Get headers with proper attribution for analytics."""
        return {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": self.config.site_url,
            "X-Title": self.config.site_name,
        }

    def _get_payload(self, messages: list[dict[str, str]], **kwargs) -> dict[str, Any]:
        """Build the request payload."""
        return {
            "model": kwargs.get("model", self.config.model),
            "messages": messages,
            "temperature": kwargs.get("temperature", self.config.temperature),
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
            "stream": False,
        }

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def chat_completion(
        self, messages: list[dict[str, str]], **kwargs
    ) -> dict[str, Any]:
        """
        Make a synchronous chat completion request to OpenRouter with proper attribution.

        Args:
            messages: List of message dictionaries with 'role' and 'content'
            **kwargs: Additional parameters (model, temperature, max_tokens)

        Returns:
            API response dictionary
        """
        url = f"{self.BASE_URL}/chat/completions"
        headers = self._get_headers()
        payload = self._get_payload(messages, **kwargs)

        logger.info(f"Making OpenRouter API call to {url}")
        logger.debug(f"Headers: {headers}")
        logger.debug(f"Payload: {json.dumps(payload, indent=2)}")

        start_time = time.time()

        try:
            response = self.client.post(url=url, headers=headers, json=payload)
            response.raise_for_status()

            result = response.json()
            latency = time.time() - start_time

            logger.info(f"OpenRouter API call successful. Model: {payload['model']}")

            # Record metrics
            tokens_used = 0
            if "usage" in result:
                usage = result["usage"]
                tokens_used = usage.get("total_tokens", 0)
                logger.info(f"Tokens used: {tokens_used}")

            self.metrics.record_request(True, latency, tokens_used)

            return result

        except httpx.HTTPError as e:
            latency = time.time() - start_time
            self.metrics.record_request(False, latency)

            logger.error(f"OpenRouter API call failed: {e}")
            logger.error(
                f"Response: {e.response.text if hasattr(e, 'response') and e.response else 'No response'}"
            )
            raise

    def list_models(self) -> list[dict[str, Any]]:
        """List available models from OpenRouter."""
        url = f"{self.BASE_URL}/models"
        headers = self._get_headers()

        try:
            response = self.client.get(url=url, headers=headers)
            response.raise_for_status()
            return response.json()["data"]
        except httpx.HTTPError as e:
            logger.error(f"Failed to list models: {e}")
            raise

    def validate_model(self, model: str) -> bool:
        """Validate if a model is available."""
        try:
            models = self.list_models()
            available_models = [m["id"] for m in models]
            return model in available_models
        except Exception:
            return False

    def get_metrics(self) -> dict[str, Any]:
        """Get current API metrics."""
        return self.metrics.get_metrics()

    def close(self):
        """Close the HTTP client."""
        self.client.close()
