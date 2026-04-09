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

from unittest.mock import AsyncMock, patch

from unittest.mock import AsyncMock, patch, MagicMock

@pytest.mark.asyncio
async def test_prompt_chainer():
    chainer = PromptChainer(endpoint_url="http://127.0.0.1:8001")

    mock_response = MagicMock()
    mock_response.json.return_value = {"generated_text": "Mocked Step"}
    mock_response.raise_for_status = MagicMock()

    with patch.object(chainer.client, 'post', return_value=mock_response) as mock_post:
        # For an AsyncClient, post is async, so we need to return the sync mock object from an async coroutine.
        mock_post_async = AsyncMock(return_value=mock_response)
        chainer.client.post = mock_post_async

        steps = ["step1", "step2"]
        results = await chainer.execute_chain(steps)

        assert len(results) == 2
        assert results[0] == "Mocked Step"
        assert results[1] == "Mocked Step"

        decomposition = await chainer.decompose_task("Complex Goal")
        assert len(decomposition) == 1 # "Mocked Step"

    await chainer.close()
