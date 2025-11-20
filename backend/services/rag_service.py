from typing import List, Dict, Any, Tuple

from ..core.llm_client import llm_client


class RAGService:
    """
    Service RAG qui utilise llm_client.generate_with_rag
    et adapte le résultat au format attendu par RAGAgent.
    """

    async def answer_question(self, question: str) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Retourne (réponse_texte, documents_de_contexte)
        - réponse_texte : str
        - documents_de_contexte : liste de dicts (sources RAG)
        """
        # 👉 On délègue tout le boulot RAG (retrieval + LLM) au LLMClient
        result = await llm_client.generate_with_rag(question)

        answer = result.get("answer", "(Pas de réponse)")
        docs = result.get("sources", [])

        return answer, docs


rag_service = RAGService()
