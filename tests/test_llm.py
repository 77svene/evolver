import pytest
import asyncio
from src.marketing_organism.llm.service import FastAPIService
from src.marketing_organism.llm.reasoning import PromptChainer
from httpx import AsyncClient, ASGITransport

@pytest.mark.asyncio
async def test_llm_service():
    service = FastAPIService(port=8001)

    # Simple direct testing of endpoints using FastAPIService's internal app directly
    from src.marketing_organism.llm.service import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/generate", json={"prompt": "test"})
        assert response.status_code == 200
        assert "mocked" in response.json()["generated_text"].lower()

@pytest.mark.asyncio
async def test_prompt_chainer():
    # We will mock httpx.AsyncClient.post to avoid actually spinning up the server
    # and relying on port availability during tests
    chainer = PromptChainer(endpoint_url="http://127.0.0.1:8001")

    class MockResponse:
        def __init__(self, data):
            self._data = data
        def json(self):
            return self._data
        def raise_for_status(self):
            pass

    async def mock_post(url, **kwargs):
        if url.endswith("/generate"):
            return MockResponse({"generated_text": "Mocked Step"})
        return MockResponse({})

    chainer.client.post = mock_post

    steps = ["step1", "step2"]
    results = await chainer.execute_chain(steps)

    assert len(results) == 2
    assert results[0] == "Mocked Step"
    assert results[1] == "Mocked Step"

    decomposition = await chainer.decompose_task("Complex Goal")
    assert len(decomposition) == 1 # "Mocked Step"

    await chainer.close()
