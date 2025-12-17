from typing import List, Dict, Any, Tuple
import re

from ..core.llm_client import llm_client
from .. import state

from rag.corpus.rag_lab_esilv import (
    retrieve_docs,
    build_prompt,
    load_uploaded_file_chunks,
    normalize_source_name,
)


def question_mentions_uploaded_doc(question: str, filename: str) -> bool:
    """
    Retourne True si la question semble parler explicitement du document uploadé.
    (sinon: on ne force pas le RAG sur l'upload)
    """
    if not filename:
        return False

    q = (question or "").lower()
    name = filename.lower()

    # déclencheurs explicites
    triggers = [
        "document",
        "pdf",
        "fichier",
        "pièce jointe",
        "upload",
        "que j'ai envoyé",
        "que j'ai importé",
        "selon le document",
        "dans le document",
        "dans le pdf",
        "dans le fichier",
        "ci-joint",
        name,  # si l'utilisateur mentionne le nom
    ]

    return any(t in q for t in triggers)


class RAGService:
    """
    Service RAG : FAISS + (optionnel) priorité au dernier fichier uploadé.
    Fallback: si le fichier uploadé n'est pas encore indexé, on le charge localement
    et on sélectionne les meilleurs chunks.

    IMPORTANT:
    - On ne force l'upload QUE si la question semble parler du document.
    """

    async def answer_question(self, question: str) -> Tuple[str, List[Dict[str, Any]]]:
        # 1) FAISS retrieval sur tout le corpus
        docs = retrieve_docs(question, k=20)

        # 2) priorité au dernier upload uniquement si la question le mentionne
        last_name = getattr(state, "LAST_UPLOADED_FILENAME", None)
        if last_name and question_mentions_uploaded_doc(question, last_name):
            last_low = last_name.lower()

            # 2a) essayer de filtrer parmi les docs FAISS
            filtered = []
            for d in docs:
                meta = d.metadata or {}
                src = normalize_source_name(str(meta.get("source") or ""))
                if last_low in src and "uploads" in src:
                    filtered.append(d)

            if filtered:
                docs = filtered
            else:
                # 2b) fallback : charger le fichier local + top chunks (si pas indexé)
                fallback_chunks = load_uploaded_file_chunks(last_name, question, top_k=8)
                if fallback_chunks:
                    docs = fallback_chunks

        # 3) prompt
        prompt = build_prompt(docs, question)

        # 4) LLM
        answer = await llm_client.generate(prompt=prompt)

        # 5) nettoyage sources éventuelles
        answer_clean = re.sub(r"\[source:[^\]]*\]", "", answer, flags=re.IGNORECASE)
        answer_clean = re.sub(r"\s{2,}", " ", answer_clean).strip()

        # 6) context_docs pour le frontend
        context_docs: List[Dict[str, Any]] = []
        for d in docs:
            meta = d.metadata or {}
            context_docs.append(
                {
                    "source": meta.get("source"),
                    "page": meta.get("page", "N/A"),
                    "url": meta.get("url") or meta.get("source_url"),
                    "snippet": (d.page_content or "")[:500],
                }
            )

        return answer_clean, context_docs


rag_service = RAGService()
