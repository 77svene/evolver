from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import asyncio
import logging
import httpx
import os

app = FastAPI(title="Local LLM Service Wrapper")
logger = logging.getLogger("llm_service")

# Optionally configure this to point to a real local Ollama/OpenAI API compatible backend
LLM_BACKEND_URL = os.getenv("LLM_BACKEND_URL", "http://127.0.0.1:11434/api/generate")

class GenerateRequest(BaseModel):
    prompt: str
    max_tokens: int = 256
    temperature: float = 0.7
    model: str = "qwen"

class EmbedRequest(BaseModel):
    text: str
    model: str = "nomic-embed-text"

class GenerateResponse(BaseModel):
    generated_text: str

class EmbedResponse(BaseModel):
    embeddings: list[float]

@app.post("/generate", response_model=GenerateResponse)
async def generate(req: GenerateRequest):
    logger.info(f"Received generation request: {req.prompt[:50]}...")

    # Attempt to proxy the request to a real local LLM backend if configured and reachable
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(LLM_BACKEND_URL, json={
                "model": req.model,
                "prompt": req.prompt,
                "stream": False,
                "options": {
                    "temperature": req.temperature,
                    "num_predict": req.max_tokens
                }
            })
            response.raise_for_status()
            data = response.json()
            return {"generated_text": data.get("response", "")}
    except Exception as e:
        logger.warning(f"Failed to reach actual LLM backend ({e}). Falling back to mocked generation.")
        await asyncio.sleep(0.5)
        return {"generated_text": f"Mocked fallback LLM generation for prompt '{req.prompt}'"}

@app.post("/embed", response_model=EmbedResponse)
async def embed(req: EmbedRequest):
    logger.info("Received embedding request")

    embed_url = LLM_BACKEND_URL.replace("/generate", "/embeddings")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(embed_url, json={
                "model": req.model,
                "prompt": req.text
            })
            response.raise_for_status()
            data = response.json()
            return {"embeddings": data.get("embedding", [])}
    except Exception as e:
        logger.warning(f"Failed to reach actual LLM backend for embedding ({e}). Falling back to mocked extraction.")
        await asyncio.sleep(0.1)
        return {"embeddings": [0.1, 0.2, 0.3, 0.4]}

class FastAPIService:
    def __init__(self, host="127.0.0.1", port=8000):
        self.host = host
        self.port = port
        self.server = None

    def start(self):
        import uvicorn
        config = uvicorn.Config(app, host=self.host, port=self.port, loop="asyncio")
        self.server = uvicorn.Server(config)
        return self.server.serve()

    async def stop(self):
        if self.server:
            self.server.should_exit = True
