import httpx
from typing import List, Dict, Any
import logging

class PromptChainer:
    def __init__(self, endpoint_url="http://127.0.0.1:8000"):
        self.endpoint_url = endpoint_url
        self.client = httpx.AsyncClient()

    async def _call_llm(self, prompt: str, timeout: float = 60.0) -> str:
        try:
            response = await self.client.post(
                f"{self.endpoint_url}/generate",
                json={"prompt": prompt, "max_tokens": 1024, "temperature": 0.3},
                timeout=timeout
            )
            response.raise_for_status()
            data = response.json()
            return data.get("generated_text", "")
        except Exception as e:
            logging.error(f"Error calling LLM: {e}")
            return ""

    async def execute_chain(self, task_list: List[str]) -> List[str]:
        """Executes a sequence of subtasks as a sequential prompt chain."""
        results = []
        context = ""
        for i, task in enumerate(task_list):
            prompt = f"Task: {task}\nContext: {context}\nPlease generate the next step or output."
            output = await self._call_llm(prompt)
            results.append(output)
            context += f"\nResult {i}: {output}"

        return results

    async def decompose_task(self, goal: str) -> List[str]:
        """Decomposes a high-level goal into actionable sub-tasks."""
        prompt = f"Decompose the following goal into a sequence of actionable steps:\nGoal: {goal}"
        result = await self._call_llm(prompt)

        # In a real implementation, parse result into a list of steps.
        # Mock parsing:
        steps = [step.strip() for step in result.split('\n') if step.strip()]
        return steps if steps else ["Perform task execution"]

    async def close(self):
        await self.client.aclose()
