from typing import List

from ..core.llm_client import llm_client


class RAGService:
    """
    Service RAG :
    - retrieve des passages pertinents (ici encore simulés)
    - appelle le LLM avec le contexte
    """

    def __init__(self):
        # TODO: charger ici ton vector store / index (Chroma, FAISS, etc.)
        self.index_ready = False

    async def retrieve_context(self, query: str, k: int = 5) -> List[str]:
        """
        Récupère les k documents les plus pertinents.
        Pour l'instant, stub.
        """
        # TODO: faire un vrai retrieval sur ta base ESILV
        return [
            "L’ESILV est une école d’ingénieurs généraliste située à Paris-La Défense.",
            "Les programmes couvrent l’ingénierie financière, l’informatique, la data, l’IA, l’énergie, la mécanique numérique, etc.",
            "Les admissions sont possibles via Parcoursup, concours, admissions parallèles, et programmes internationaux.",
        ][:k]

    async def answer_question(self, question: str) -> tuple[str, List[str]]:
        """
        Utilise le RAG : retrieval + génération avec Ollama Mistral.
        """
        context_docs = await self.retrieve_context(question)
        context_str = "\n\n".join(context_docs)

        system_prompt = (
            "Tu es un assistant intelligent pour l'école d'ingénieurs ESILV. "
            "Tu réponds en français, de manière claire et structurée. "
            "Si une information n'est pas disponible dans le contexte, dis-le franchement "
            "et reste général sans inventer de détails."
        )

        user_prompt = f"""
Contexte (extraits de la base documentaire) :
{context_str}

Question de l'utilisateur :
{question}

Réponse en français, claire et concise :
"""

        answer = await llm_client.generate(prompt=user_prompt, system_prompt=system_prompt)
        return answer, context_docs


rag_service = RAGService()