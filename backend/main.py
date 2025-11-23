from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .core.settings import settings
from .routers import chat, admin

from pathlib import Path
import shutil
from rag.corpus.rag_lab_esilv import build_index
from . import state

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
    )


    # CORS : autoriser frontend

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.FRONTEND_ORIGIN, "http://localhost:3000", "*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


    # Inclusion des routers
    app.include_router(chat.router, prefix=settings.API_V1_PREFIX)
    app.include_router(admin.router, prefix=settings.API_V1_PREFIX)


    @app.get("/")
    async def root():
        return {"message": "ESILV Smart Assistant backend is running."}

    
    # UPLOAD DOCUMENTS
    
    UPLOAD_DIR = Path("rag/corpus/uploads")
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    @app.post(f"{settings.API_V1_PREFIX}/upload-document")
    async def upload_document(file: UploadFile = File(...)):
        if not file.filename:
            raise HTTPException(status_code=400, detail="Fichier sans nom.")

        filename = Path(file.filename).name
        dest_path = UPLOAD_DIR / filename

        try:
            with dest_path.open("wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Erreur lors de l'enregistrement du fichier : {e}",
            )
        # 🟢 ENREGISTRER LE DERNIER FICHIER UPLOADÉ (PDF / DOCX / TXT)
        state.LAST_UPLOADED_FILENAME = filename
        # 🔁 Réindexation du RAG après chaque upload
        try:
            build_index()
        except Exception as e:
            # On log l'erreur mais on ne bloque pas totalement l'upload
            raise HTTPException(
                status_code=500,
                detail=f"Fichier sauvegardé, mais erreur lors de la reconstruction de l'index RAG : {e}",
            )

        return {
            "message": "Fichier uploadé et index RAG reconstruit.",
            "filename": filename,
            "path": str(dest_path),
        }


    return app



# APP INSTANCE

app = create_app()
