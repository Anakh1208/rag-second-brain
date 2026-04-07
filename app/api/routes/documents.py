from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from pathlib import Path
import uuid
import json
from datetime import datetime

router = APIRouter()

BASE_DIR = Path(__file__).parent.parent.parent.parent
VAULT_DIR = BASE_DIR / "data" / "vault" / "documents"
METADATA_DIR = BASE_DIR / "data" / "metadata"

VAULT_DIR.mkdir(parents=True, exist_ok=True)
METADATA_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".txt", ".pdf"}

@router.post("/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Only PDF and TXT allowed")

    doc_id = str(uuid.uuid4())
    file_path = VAULT_DIR / f"{doc_id}{ext}"

    content = await file.read()
    file_path.write_bytes(content)

    metadata = {
        "document_id": doc_id,
        "filename": file.filename,
        "uploaded_at": datetime.utcnow().isoformat(),
        "vault_path": str(file_path),
        "chunks": []  # IMPORTANT for RAG later
    }

    metadata_file = METADATA_DIR / f"{doc_id}.json"
    metadata_file.write_text(json.dumps(metadata, indent=2))

    return JSONResponse(
        status_code=201,
        content={
            "success": True,
            "document_id": doc_id,
            "filename": file.filename
        }
    )


@router.get("/documents")
async def list_documents():
    docs = []
    for f in METADATA_DIR.glob("*.json"):
        docs.append(json.loads(f.read_text()))
    return {"success": True, "documents": docs}
