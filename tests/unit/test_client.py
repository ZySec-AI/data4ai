"""Tests for synchronous and asynchronous OpenRouter clients."""

from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest

from data4ai.client import OpenRouterClient, OpenRouterConfig, SyncOpenRouterClient


def test_config_headers_and_payload():
    config = OpenRouterConfig("key", model="default", temperature=0.5, max_tokens=100)
    with patch("data4ai.client.httpx.Client"):
        client = SyncOpenRouterClient(config)

    assert client._get_headers()["Authorization"] == "Bearer key"
    assert client._get_payload(
        [{"role": "user", "content": "hello"}],
        model="override",
        temperature=0.2,
        max_tokens=50,
    ) == {
        "model": "override",
        "messages": [{"role": "user", "content": "hello"}],
        "temperature": 0.2,
        "max_tokens": 50,
        "stream": False,
    }


def test_sync_client_success_models_metrics_and_close():
    response = Mock()
    response.json.return_value = {"usage": {"total_tokens": 12}, "choices": []}
    with patch("data4ai.client.httpx.Client") as client_class:
        client_class.return_value.post.return_value = response
        client_class.return_value.get.return_value.json.return_value = {
            "data": [{"id": "model"}]
        }
        client = SyncOpenRouterClient(OpenRouterConfig("key"))
        client.metrics = Mock()

        assert (
            client.chat_completion([{"role": "user", "content": "hello"}])["choices"]
            == []
        )
        client.metrics.record_request.assert_called_once()
        assert client.list_models() == [{"id": "model"}]
        assert client.validate_model("model") is True
        assert client.validate_model("missing") is False
        client.metrics.get_metrics.return_value = {"requests": 1}
        assert client.get_metrics() == {"requests": 1}
        client.close()
        client_class.return_value.close.assert_called_once()


def test_sync_client_errors_without_retry_delay():
    request = httpx.Request("GET", "https://example.test")
    error = httpx.HTTPStatusError(
        "bad", request=request, response=httpx.Response(500, request=request)
    )
    with patch("data4ai.client.httpx.Client") as client_class:
        client = SyncOpenRouterClient(OpenRouterConfig("key"))
        client.metrics = Mock()
        client_class.return_value.get.side_effect = error
        with pytest.raises(httpx.HTTPStatusError):
            client.list_models()
        client.list_models = Mock(side_effect=error)
        assert client.validate_model("model") is False


@pytest.mark.asyncio
async def test_async_client_success_models_metrics_and_close():
    response = Mock()
    response.json.return_value = {"usage": {"total_tokens": 7}, "choices": []}
    models_response = Mock()
    models_response.json.return_value = {"data": [{"id": "model"}]}
    with patch("data4ai.client.httpx.AsyncClient") as client_class:
        client_class.return_value.post = AsyncMock(return_value=response)
        client_class.return_value.get = AsyncMock(return_value=models_response)
        client_class.return_value.aclose = AsyncMock()
        client = OpenRouterClient(OpenRouterConfig("key"))
        client.rate_limiter = AsyncMock()
        client.metrics = Mock()

        assert await client.chat_completion([{"role": "user", "content": "hello"}]) == {
            "usage": {"total_tokens": 7},
            "choices": [],
        }
        assert await client.list_models() == [{"id": "model"}]
        assert await client.validate_model("model") is True
        client.list_models = AsyncMock(side_effect=RuntimeError("offline"))
        assert await client.validate_model("model") is False
        client.metrics.get_metrics.return_value = {"requests": 1}
        assert client.get_metrics() == {"requests": 1}
        await client.close()
        client_class.return_value.aclose.assert_awaited_once()
