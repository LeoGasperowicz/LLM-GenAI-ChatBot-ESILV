from typing import Literal, List, Dict, Any
import httpx

from .settings import settings
from rag.corpus.rag_lab_esilv import answer_with_rag as rag_answer_with_rag


class LLMClient:
    def __init__(self, provider: Literal["ollama", "gcp", "local"] | None = None):
        # Provider (ollama, gcp, local...) – dans ton projet on utilise "ollama"
        self.provider = provider or settings.LLM_PROVIDER
        self.model = settings.LLM_MODEL
        self.base_url = settings.OLLAMA_BASE_URL

    async def generate(self, prompt: str, system_prompt: str | None = None) -> str:
        """
        Appel LLM "brut" (sans RAG).
        Utilisé par :
        - l'orchestrateur pour classifier l'intent (faq / contact / unknown)
        - potentiellement d'autres agents "simples".
        """
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

        async with httpx.AsyncClient(base_url=self.base_url, timeout=120.0) as client:
            resp = await client.post("/api/chat", json=payload)
            resp.raise_for_status()
            data = resp.json()

        # Format standard d'Ollama : {"message": {"content": "..."}}
        try:
            content = data["message"]["content"]
        except Exception:
            content = str(data)

        return content

    async def generate_with_rag(self, question: str) -> Dict[str, Any]:
        """
        Appel LLM **avec RAG ESILV**.
        - Récupère les documents pertinents (PDF + TXT) via FAISS
        - Construit un prompt de contexte (dans rag_lab_esilv.answer_with_rag)
        - Appelle generate() comme LLM interne

        Retourne un dict :
        {
            "answer": str,
            "sources": [  # liste de chunks/documents utilisés
                {
                    "source": ...,
                    "page": ...,
                    "url": ...,
                    "snippet": ...,
                    ...
                },
                ...
            ]
        }
        """

        async def _llm_call(prompt: str) -> str:
            # On laisse le RAG construire le prompt complet, donc pas de system_prompt ici
            return await self.generate(prompt)

        # rag_answer_with_rag est défini dans rag/corpus/rag_lab_esilv.py
        result = await rag_answer_with_rag(question, llm_call=_llm_call)
        # result est déjà de la forme {"answer": ..., "sources": [...]}
        return result


# Instance globale utilisée partout dans le backend
llm_client = LLMClient()
