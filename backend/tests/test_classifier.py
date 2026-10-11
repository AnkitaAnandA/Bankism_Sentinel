import httpx
import pytest

from app.config import Settings
from app.security.llm_classifier import LLMClassifier


@pytest.mark.parametrize("mode", ["malformed", "timeout", "http_error"])
async def test_fail_closed(mode):
    calls = 0

    async def handler(request):
        nonlocal calls
        calls += 1
        if mode == "timeout":
            raise httpx.ReadTimeout("timeout")
        if mode == "http_error":
            return httpx.Response(503)
        return httpx.Response(
            200,
            json={
                "candidates": [
                    {"content": {"parts": [{"text": '{"is_injection":"false"}'}]}}
                ]
            },
        )

    cfg = Settings(
        intent_hmac_key="a" * 64,
        session_signing_key="b" * 64,
        llm_api_key="test",
        llm_failure_threshold=1,
    )
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        classifier = LLMClassifier(cfg, client)
        assert await classifier.classify("Transfer ₹500 to Rahul") is None
        assert not classifier.healthy()
        previous = calls
        assert await classifier.classify("Transfer ₹600 to Rahul") is None
        assert calls == previous
        assert previous <= 2
