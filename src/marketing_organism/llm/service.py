from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import asyncio
import logging

app = FastAPI(title="Local LLM Service Wrapper")
logger = logging.getLogger("llm_service")

class GenerateRequest(BaseModel):
    prompt: str
    max_tokens: int = 256
    temperature: float = 0.7

class EmbedRequest(BaseModel):
    text: str

class GenerateResponse(BaseModel):
    generated_text: str

class EmbedResponse(BaseModel):
    embeddings: list[float]

@app.post("/generate", response_model=GenerateResponse)
async def generate(req: GenerateRequest):
    logger.info(f"Received generation request: {req.prompt[:50]}...")
    # Mocking actual model inference
    await asyncio.sleep(0.5)
    return {"generated_text": f"Mocked LLM generation for prompt '{req.prompt}'"}

@app.post("/embed", response_model=EmbedResponse)
async def embed(req: EmbedRequest):
    logger.info("Received embedding request")
    # Mocking embedding extraction
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
