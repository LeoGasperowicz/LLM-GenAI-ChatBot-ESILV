from pathlib import Path
from typing import List, Dict, Any

from langchain_community.document_loaders import (
    PyPDFLoader,
    DirectoryLoader,
    TextLoader,
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS


# ============
#  CHEMINS
# ============

# dossier où se trouve CE fichier : rag/corpus
# (si ce fichier est dans rag/corpus/rag_lab_esilv.py)
BASE_DIR = Path(__file__).resolve().parent  # -> rag/corpus

PDF_DIR = BASE_DIR / "pdf"      # tes PDFs : rag/corpus/pdf
TXT_DIR = BASE_DIR / "html"     # tes .txt issus du scraping : rag/corpus/html
INDEX_DIR = BASE_DIR / "vector_store_faiss"

EMB_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


# ============
#  CHARGEMENT
# ============

def load_pdfs():
    if not PDF_DIR.exists():
        print(f"⚠ Dossier PDF inexistant : {PDF_DIR}")
        return []

    print(f"📄 Chargement des PDFs depuis : {PDF_DIR}")
    loader = DirectoryLoader(
        str(PDF_DIR),
        glob="**/*.pdf",     # ← corrigé (avant: "/*.pdf")
        loader_cls=PyPDFLoader,
    )
    docs = loader.load()
    print(f"   → {len(docs)} documents PDF chargés")
    return docs


def load_txts():
    if not TXT_DIR.exists():
        print(f"⚠ Dossier TXT inexistant : {TXT_DIR}")
        return []

    print(f"📝 Chargement des TXT depuis : {TXT_DIR}")
    loader = DirectoryLoader(
        str(TXT_DIR),
        glob="**/*.txt",   # ne prendra que les fichiers .txt
        loader_cls=TextLoader,
        loader_kwargs={
            "encoding": "utf-8",
            "autodetect_encoding": True,  # laisse TextLoader essayer de deviner si besoin
        },
    )
    docs = loader.load()
    print(f"   → {len(docs)} documents TXT chargés")
    return docs


# ============
#  BUILD INDEX
# ============

def build_index():
    INDEX_DIR.mkdir(parents=True, exist_ok=True)

    pdf_docs = load_pdfs()
    txt_docs = load_txts()
    docs = pdf_docs + txt_docs

    if not docs:
        print("❌ Aucun document trouvé, index non créé.")
        return

    print(f"📚 Total documents (PDF + TXT) : {len(docs)}")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150,
    )
    chunks = splitter.split_documents(docs)
    print(f"   → {len(chunks)} chunks créés")

    embeddings = HuggingFaceEmbeddings(model_name=EMB_MODEL)

    vectorstore = FAISS.from_documents(chunks, embeddings)
    vectorstore.save_local(str(INDEX_DIR))

    print(f"✅ Index FAISS sauvegardé dans : {INDEX_DIR}")


# ============
#  UTILISATION
# ============

def load_vectorstore() -> FAISS:
    embeddings = HuggingFaceEmbeddings(model_name=EMB_MODEL)
    vs = FAISS.load_local(
        str(INDEX_DIR),
        embeddings,
        allow_dangerous_deserialization=True,
    )
    return vs


def retrieve_docs(query: str, k: int = 4):
    vs = load_vectorstore()
    return vs.similarity_search(query, k=k)


def build_prompt(docs, query: str) -> str:
    """
    Construit un prompt pour ton LLM (Ollama, Gemini, etc.)
    en incluant les sources (metadata.source, metadata.page).
    """
    blocks = []
    for i, d in enumerate(docs):
        source = d.metadata.get("source", f"doc_{i}")
        page = d.metadata.get("page", "N/A")
        blocks.append(f"[source:{source}, page:{page}]\n{d.page_content}")

    context_text = "\n\n".join(blocks)

    prompt = f"""
Tu es un assistant pour les étudiants et futurs étudiants de l'ESILV.
Utilise UNIQUEMENT les informations du contexte ci-dessous pour répondre.
Pour chaque fait important, cite la source comme [source:..., page:...].

Contexte :
{context_text}

Question :
{query}

Réponds en français, de manière claire et structurée, avec les citations.
"""
    return prompt


# =======================================
#  FONCTION UTILISABLE DANS L'APPLICATION
# =======================================

async def answer_with_rag(question: str, llm_call) -> Dict[str, Any]:
    """
    Fonction à utiliser dans ton backend.

    - question : question utilisateur
    - llm_call : coroutine ou fonction async qui prend un prompt (str)
                 et retourne la réponse du LLM (str)
                 ex: llm_call(prompt) -> "texte de réponse"

    Retourne un dict :
    {
        "answer": str,
        "sources": [
            {
                "source": str,
                "page": int | "N/A",
                "metadata": {...},
                "snippet": str,
            },
            ...
        ]
    }
    """
    docs = retrieve_docs(question, k=4)
    prompt = build_prompt(docs, question)
    answer = await llm_call(prompt)

    sources = []
    for i, d in enumerate(docs):
        meta = d.metadata or {}
        sources.append({
            "source": meta.get("source", f"doc_{i}"),
            "page": meta.get("page", "N/A"),
            "metadata": meta,
            "snippet": d.page_content[:500] + ("..." if len(d.page_content) > 500 else ""),
        })

    return {
        "answer": answer,
        "sources": sources,
    }


# ============
#  CLI SIMPLE
# ============

if __name__ == "__main__":   # ← corrigé (avant: _name_)
    import argparse
    import asyncio

    async def dummy_llm(prompt: str) -> str:
        # Pour test rapide : renvoie juste le prompt tronqué
        return "LLM (dummy) recevrait ce prompt :\n\n" + prompt[:1000]

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--build",
        action="store_true",
        help="(Re)construit l'index FAISS à partir des PDFs + TXT",
    )
    parser.add_argument(
        "question",
        nargs="?",
        help="Question pour tester le RAG (optionnel)",
    )
    args = parser.parse_args()

    if args.build or not INDEX_DIR.exists():
        print("🔧 Construction de l'index RAG...")
        build_index()

    if args.question:
        result = asyncio.run(answer_with_rag(args.question, dummy_llm))
        print("\n================= RÉPONSE =================\n")
        print(result["answer"])
        print("\n================= SOURCES =================\n")
        for s in result["sources"]:
            print(f"- {s['source']} (page {s['page']})")
    else:
        print("✅ Index construit. Pour tester :")
        print('   python rag/corpus/rag_lab_esilv.py --build')
        print('   python rag/corpus/rag_lab_esilv.py "Ta question ici"')
