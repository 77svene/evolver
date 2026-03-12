"""Reasoning module providing prompt chaining and LLM interaction logic."""

import logging
from typing import List

import httpx
from src.marketing_organism.exceptions import LLMIntegrationError

logger = logging.getLogger(__name__)

class PromptChainer:
    """Manages sequential execution of LLM tasks and multi-step reasoning.

    Attributes:
        endpoint_url: The URL to the local FastAPI wrapper endpoint.
        client: The asynchronous HTTP client.
    """

    def __init__(self, endpoint_url: str = "http://127.0.0.1:8000") -> None:
        """Initializes the PromptChainer.

        Args:
            endpoint_url: The base URL of the LLM generation service.
        """
        self.endpoint_url = endpoint_url
        self.client = httpx.AsyncClient()

    async def _call_llm(self, prompt: str, timeout: float = 60.0) -> str:
        """Sends a prompt to the LLM backend.

        Args:
            prompt: The instruction text to send.
            timeout: Max time in seconds to wait for a response.

        Returns:
            The generated text string from the LLM.
        """
        try:
            response = await self.client.post(
                f"{self.endpoint_url}/generate",
                json={"prompt": prompt, "max_tokens": 1024, "temperature": 0.3},
                timeout=timeout
            )
            response.raise_for_status()
            data = response.json()
            return str(data.get("generated_text", ""))
        except httpx.RequestError as e:
            logger.error(f"LLMIntegrationError: Request failed: {e}", exc_info=True)
            return ""
        except httpx.HTTPStatusError as e:
            logger.error(f"LLMIntegrationError: HTTP error {e.response.status_code}: {e}", exc_info=True)
            return ""
        except Exception as e:
            logger.error(f"LLMIntegrationError: Unexpected error calling LLM: {e}", exc_info=True)
            return ""

    async def execute_chain(self, task_list: List[str]) -> List[str]:
        """Executes a sequence of subtasks as a sequential prompt chain.

        Args:
            task_list: A list of tasks to execute in order.

        Returns:
            A list of string outputs corresponding to each task result.
        """
        results = []
        context = ""
        for i, task in enumerate(task_list):
            prompt = f"Task: {task}\nContext: {context}\nPlease generate the next step or output."
            output = await self._call_llm(prompt)
            results.append(output)
            context += f"\nResult {i}: {output}"

        return results

    async def decompose_task(self, goal: str) -> List[str]:
        """Decomposes a high-level goal into actionable sub-tasks.

        Args:
            goal: The overarching objective to be broken down.

        Returns:
            A list of smaller, actionable step descriptions.
        """
        prompt = f"Decompose the following goal into a sequence of actionable steps:\nGoal: {goal}"
        result = await self._call_llm(prompt)

        # In a real implementation, parse result into a list of steps.
        # Mock parsing:
        steps = [step.strip() for step in result.split('\n') if step.strip()]
        return steps if steps else ["Perform task execution"]

    async def close(self) -> None:
        """Closes the underlying HTTP client session."""
        await self.client.aclose()
