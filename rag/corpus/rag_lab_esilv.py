from pathlib import Path
from typing import Dict, Any, Optional
import re

from langchain_community.document_loaders import (
    PyPDFLoader,
    DirectoryLoader,
    TextLoader,
    Docx2txtLoader,
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS


# ======================
#  PATHS (robustes)
# ======================

BASE_DIR = Path(__file__).resolve().parent           # rag/corpus
PROJECT_ROOT = BASE_DIR.parent.parent                # racine projet

PDF_DIR = BASE_DIR / "pdf"
TXT_DIR = BASE_DIR / "html"

UPLOADS_DIR = BASE_DIR / "uploads"
if not UPLOADS_DIR.exists():
    UPLOADS_DIR = PROJECT_ROOT / "uploads"

INDEX_DIR = BASE_DIR / "vector_store_faiss"
if not INDEX_DIR.exists():
    INDEX_DIR = PROJECT_ROOT / "vector_store_faiss"


# ======================
#  EMBEDDINGS / SPLITTER
# ======================

EMB_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDINGS = HuggingFaceEmbeddings(model_name=EMB_MODEL)

SPLITTER = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=150,
)

_VECTORSTORE: Optional[FAISS] = None


# ======================
#  HELPERS
# ======================

def normalize_source_name(s: str) -> str:
    s = (s or "").strip().lower()
    return s.replace("\\", "/")


def enrich_docs_with_filename(docs):
    enriched = []
    for d in docs:
        meta = d.metadata or {}
        source = meta.get("source", "")

        if source:
            try:
                filename = Path(source).name
            except Exception:
                filename = source.split("/")[-1].split("\\")[-1]
        else:
            filename = "document_sans_nom"

        header_lines = [f"Nom du document : {filename}"]
        url = meta.get("url") or meta.get("source_url")
        if url:
            header_lines.append(f"Source : {url}")

        header = "\n".join(header_lines)
        d.page_content = f"{header}\n\n{d.page_content}"
        enriched.append(d)

    return enriched


# ======================
#  LOADERS (corpus)
# ======================

def load_pdfs():
    if not PDF_DIR.exists():
        print(f"⚠ Dossier PDF inexistant : {PDF_DIR}")
        return []
    loader = DirectoryLoader(str(PDF_DIR), glob="**/*.pdf", loader_cls=PyPDFLoader)
    return loader.load()


def load_txts():
    if not TXT_DIR.exists():
        print(f"⚠ Dossier TXT inexistant : {TXT_DIR}")
        return []
    loader = DirectoryLoader(
        str(TXT_DIR),
        glob="**/*.txt",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8", "autodetect_encoding": True},
    )
    return loader.load()


def load_uploaded_docs():
    if not UPLOADS_DIR.exists():
        print(f"⚠ Dossier UPLOADS inexistant : {UPLOADS_DIR}")
        return []

    docs = []

    pdf_loader = DirectoryLoader(str(UPLOADS_DIR), glob="**/*.pdf", loader_cls=PyPDFLoader)
    docs.extend(pdf_loader.load())

    txt_loader = DirectoryLoader(
        str(UPLOADS_DIR),
        glob="**/*.txt",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8", "autodetect_encoding": True},
    )
    docs.extend(txt_loader.load())

    docx_loader = DirectoryLoader(str(UPLOADS_DIR), glob="**/*.docx", loader_cls=Docx2txtLoader)
    docs.extend(docx_loader.load())

    return docs


# ======================
#  BUILD / LOAD INDEX
# ======================

def build_index():
    INDEX_DIR.mkdir(parents=True, exist_ok=True)

    docs = load_pdfs() + load_txts() + load_uploaded_docs()
    if not docs:
        print("❌ Aucun document trouvé, index non créé.")
        return

    docs = enrich_docs_with_filename(docs)
    chunks = SPLITTER.split_documents(docs)
    vectorstore = FAISS.from_documents(chunks, EMBEDDINGS)
    vectorstore.save_local(str(INDEX_DIR))

    print(f"✅ Index FAISS sauvegardé dans : {INDEX_DIR}")


def load_vectorstore() -> FAISS:
    global _VECTORSTORE
    if _VECTORSTORE is None:
        _VECTORSTORE = FAISS.load_local(
            str(INDEX_DIR),
            EMBEDDINGS,
            allow_dangerous_deserialization=True,
        )
    return _VECTORSTORE


def retrieve_docs(query: str, k: int = 4):
    vs = load_vectorstore()
    return vs.similarity_search(query, k=k)


# ======================
#  PROMPT
# ======================

def build_prompt(docs, query: str) -> str:
    blocks = []
    for i, d in enumerate(docs):
        meta = d.metadata or {}
        source = meta.get("source", f"doc_{i}")
        page = meta.get("page", "N/A")
        blocks.append(f"[source:{source}, page:{page}]\n{d.page_content}")

    context_text = "\n\n".join(blocks)

    return f"""
Tu es un assistant d'admission pour l'école d'ingénieurs **ESILV**.

INFORMATIONS IMPORTANTES SUR L'ÉCOLE :
- ESILV signifie « École Supérieure d'Ingénieurs Léonard de Vinci ».
- C'est une école d'ingénieurs située à Paris-La Défense, au sein du Pôle Léonard de Vinci.
- Tu NE DOIS JAMAIS réinventer ou redéfinir l'acronyme ESILV.
- Si tu dois rappeler ce que c'est, utilise exactement :
  « l’ESILV, École Supérieure d'Ingénieurs Léonard de Vinci à Paris-La Défense ».

Utilise UNIQUEMENT les informations du contexte ci-dessous pour répondre.
Pour chaque fait important, cite la source comme [source:..., page:...].

Contexte :
{context_text}

Question :
{query}

Réponds en français, clair et structuré, avec les citations.
""".strip()


# =========================================================
#  Fallback: charger un fichier uploadé non indexé + top chunks
# =========================================================

def _dot(a, b):
    return sum(x * y for x, y in zip(a, b))

def _unit_norm(v):
    n = sum(x * x for x in v) ** 0.5
    if n <= 1e-12:
        return v
    return [x / n for x in v]

def _load_single_file_as_docs(file_path: Path):
    if not file_path.exists():
        return []

    suffix = file_path.suffix.lower()
    if suffix == ".pdf":
        docs = PyPDFLoader(str(file_path)).load()
    elif suffix == ".txt":
        docs = TextLoader(str(file_path), encoding="utf-8", autodetect_encoding=True).load()
    elif suffix == ".docx":
        docs = Docx2txtLoader(str(file_path)).load()
    else:
        return []

    for d in docs:
        d.metadata = d.metadata or {}
        d.metadata["source"] = str(file_path)
        d.metadata.setdefault("page", d.metadata.get("page", "N/A"))

    return enrich_docs_with_filename(docs)

def load_uploaded_file_chunks(filename: str, question: str, top_k: int = 8):
    if not filename:
        return []

    file_path = UPLOADS_DIR / filename
    docs = _load_single_file_as_docs(file_path)
    if not docs:
        return []

    chunks = SPLITTER.split_documents(docs)
    if not chunks:
        return []

    q_emb = _unit_norm(EMBEDDINGS.embed_query(question))

    scored = []
    for ch in chunks:
        emb = EMBEDDINGS.embed_documents([ch.page_content])[0]
        emb = _unit_norm(emb)
        score = _dot(q_emb, emb)
        scored.append((score, ch))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [ch for _, ch in scored[:top_k]]


# =========================================================
#  ✅ BACKWARD COMPAT: answer_with_rag (pour llm_client.py)
# =========================================================

async def answer_with_rag(question: str, llm_call) -> Dict[str, Any]:
    """
    Conserve cette fonction car ton backend/core/llm_client.py l'importe.
    Retour:
    {
      "answer": "...",
      "sources": [{"source":..., "page":..., "metadata":..., "snippet":...}, ...]
    }
    """
    docs = retrieve_docs(question, k=20)
    prompt = build_prompt(docs, question)
    answer = await llm_call(prompt)

    sources = []
    for i, d in enumerate(docs):
        meta = d.metadata or {}
        sources.append({
            "source": meta.get("source", f"doc_{i}"),
            "page": meta.get("page", "N/A"),
            "metadata": meta,
            "snippet": (d.page_content or "")[:500] + ("..." if len((d.page_content or "")) > 500 else ""),
        })

    return {"answer": answer, "sources": sources}


# ======================
# CLI
# ======================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--build", action="store_true", help="(Re)construit l'index FAISS")
    args = parser.parse_args()

    if args.build or not INDEX_DIR.exists():
        print("🔧 Construction de l'index RAG...")
        build_index()
    else:
        print("✅ Index déjà présent.")
