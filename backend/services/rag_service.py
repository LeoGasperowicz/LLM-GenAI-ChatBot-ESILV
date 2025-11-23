from typing import List, Dict, Any, Tuple
import re

from ..core.llm_client import llm_client
from .. import state
from rag.corpus.rag_lab_esilv import retrieve_docs, build_prompt


class RAGService:
    """
    Service RAG : utilise FAISS + dernier fichier uploadé en priorité.
    """

    async def answer_question(self, question: str) -> Tuple[str, List[Dict[str, Any]]]:
        # 1️⃣ Récupération des documents via FAISS
        docs = retrieve_docs(question, k=20)

        # 2️⃣ Si un fichier a été uploadé → priorité à ce fichier
        last_name = state.LAST_UPLOADED_FILENAME
        if last_name:
            filtered_docs = []
            for d in docs:
                source_name = str(d.metadata.get("source") or "").lower()
                if last_name.lower() in source_name and "uploads" in source_name.replace("\\","/"):
                    filtered_docs.append(d)

            # Si on trouve des chunks du fichier uploadé → on remplace tous les docs par ceux-là
            if filtered_docs:
                docs = filtered_docs

        # 3️⃣ Construction du prompt RAG
        prompt = build_prompt(docs, question)

        # 4️⃣ Appel du LLM
        answer = await llm_client.generate(prompt=prompt)

        # 5️⃣ Nettoyage de la réponse (enlever [source:...])
        answer_clean = re.sub(r"\[source:[^\]]*\]", "", answer, flags=re.IGNORECASE)
        answer_clean = re.sub(r"\s{2,}", " ", answer_clean)

        # 6️⃣ Préparation des documents pour l’affichage dans Streamlit
        context_docs = []
        for d in docs:
            meta = d.metadata or {}
            context_docs.append({
                "source": meta.get("source"),
                "page": meta.get("page", "N/A"),
                "url": meta.get("url") or meta.get("source_url"),
                "snippet": d.page_content[:500],
            })

        return answer_clean, context_docs


rag_service = RAGService()