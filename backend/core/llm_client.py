from typing import Literal, List, Dict, Any
import httpx

from .settings import settings


class LLMClient:
    def __init__(self, provider: Literal["ollama", "gcp", "local"] | None = None):
        self.provider = provider or settings.LLM_PROVIDER
        self.model = settings.LLM_MODEL
        self.base_url = settings.OLLAMA_BASE_URL

    async def generate(self, prompt: str, system_prompt: str | None = None) -> str:
        if self.provider != "ollama":
            raise RuntimeError(f"Provider LLM non supporté: {self.provider}")

        messages: List[Dict[str, Any]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
        }

        async with httpx.AsyncClient(base_url=self.base_url, timeout=60.0) as client:
            resp = await client.post("/api/chat", json=payload)
            resp.raise_for_status()
            data = resp.json()

        try:
            content = data["message"]["content"]
        except Exception:
            content = str(data)

        return content


llm_client = LLMClient()
