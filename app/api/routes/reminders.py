"""
app/api/routes/documents.py
----------------------------
Document Upload and Management API Routes

Academic Note (for SEPM viva):
- Implements file upload using FastAPI's UploadFile (built on Starlette)
- Follows RESTful API design principles
- Separates concerns: routing logic vs. business logic (storage management)
- Uses UUID for unique identification (prevents filename conflicts)
- Stores raw files separately from metadata (digital vault pattern)
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, status
from fastapi.responses import JSONResponse
from typing import List
from pathlib import Path
import uuid
import json
from datetime import datetime
import logging

# PDF text extraction library
try:
    from PyPDF2 import PdfReader
except ImportError:
    PdfReader = None  # Will handle this gracefully

logger = logging.getLogger(__name__)

# ==============================================================================
# ROUTER INITIALIZATION
# ==============================================================================
router = APIRouter()

# ==============================================================================
# CONFIGURATION
# ==============================================================================
# Define base paths for storage
BASE_DIR = Path(__file__).resolve().parents[3]  # Project root
VAULT_DIR = BASE_DIR / "data" / "vault" / "documents"
METADATA_DIR = BASE_DIR / "data" / "metadata"

# Allowed file types
ALLOWED_EXTENSIONS = {".pdf", ".txt"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB limit

# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def validate_file_type(filename: str) -> bool:
    """
    Validates if the uploaded file has an allowed extension.
    
    Args:
        filename: Original filename from upload
        
    Returns:
        True if valid, False otherwise
        
    Academic Note:
    - Simple validation based on file extension
    - In production, should also check MIME type and file content
    """
    file_extension = Path(filename).suffix.lower()
    return file_extension in ALLOWED_EXTENSIONS


def extract_text_from_pdf(file_path: Path) -> str:
    """
    Extracts text content from a PDF file.
    
    Args:
        file_path: Path to the PDF file
        
    Returns:
        Extracted text as a string
        
    Academic Note:
    - Uses PyPDF2 for basic text extraction
    - May not work perfectly with scanned PDFs (would need OCR)
    - For academic prototype, basic extraction is sufficient
    """
    if PdfReader is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="PDF processing library not installed. Run: pip install PyPDF2"
        )
    
    try:
        reader = PdfReader(str(file_path))
        text_content = []
        
        # Extract text from each page
        for page in reader.pages:
            text = page.extract_text()
            if text:
                text_content.append(text)
        
        return "\n".join(text_content)
    
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to extract text from PDF: {str(e)}"
        )


def extract_text_from_txt(file_path: Path) -> str:
    """
    Reads text content from a TXT file.
    
    Args:
        file_path: Path to the TXT file
        
    Returns:
        File content as a string
        
    Academic Note:
    - Simple file reading with UTF-8 encoding
    - Handles potential encoding errors gracefully
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except UnicodeDecodeError:
        # Try with different encoding if UTF-8 fails
        try:
            with open(file_path, "r", encoding="latin-1") as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading TXT file: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to read TXT file: {str(e)}"
            )


def save_metadata(document_id: str, metadata: dict) -> None:
    """
    Saves document metadata as a JSON file.
    
    Args:
        document_id: Unique identifier for the document
        metadata: Dictionary containing document metadata
        
    Academic Note:
    - Uses JSON for human-readable storage (easy to inspect and debug)
    - In production, might use a proper database (PostgreSQL, MongoDB)
    - File-based storage is sufficient for academic prototype
    """
    metadata_file = METADATA_DIR / f"{document_id}.json"
    
    try:
        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Metadata saved: {metadata_file}")
    
    except Exception as e:
        logger.error(f"Error saving metadata: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save metadata: {str(e)}"
        )


# ==============================================================================
# API ENDPOINTS
# ==============================================================================

@router.post("/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    """
    Upload a document (PDF or TXT) to the digital vault.
    
    Request:
        - Multipart/form-data with file attachment
        - Accepts .pdf and .txt files only
        
    Response:
        - document_id: Unique identifier
        - filename: Original filename
        - file_type: Extension (.pdf or .txt)
        - upload_timestamp: ISO format timestamp
        - text_preview: First 200 characters of extracted text
        
    Academic Note (for SEPM):
    - Demonstrates file upload handling in FastAPI
    - Implements validation, storage, and metadata generation
    - Uses UUID for unique identification (prevents collisions)
    - Separates raw file storage from metadata (modularity principle)
    """
    
    # -------------------------------------------------------------------------
    # STEP 1: Validate file type
    # -------------------------------------------------------------------------
    if not validate_file_type(file.filename):
        logger.warning(f"Invalid file type attempted: {file.filename}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Only {', '.join(ALLOWED_EXTENSIONS)} files are allowed."
        )
    
    # -------------------------------------------------------------------------
    # STEP 2: Generate unique document ID
    # -------------------------------------------------------------------------
    document_id = str(uuid.uuid4())
    file_extension = Path(file.filename).suffix.lower()
    
    logger.info(f"Processing upload: {file.filename} -> {document_id}")
    
    # -------------------------------------------------------------------------
    # STEP 3: Save raw file to vault
    # -------------------------------------------------------------------------
    vault_file_path = VAULT_DIR / f"{document_id}{file_extension}"
    
    try:
        # Read file content
        content = await file.read()
        
        # Check file size
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Maximum size is {MAX_FILE_SIZE / (1024*1024)} MB."
            )
        
        # Write to vault
        with open(vault_file_path, "wb") as f:
            f.write(content)
        
        logger.info(f"File saved to vault: {vault_file_path}")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving file to vault: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}"
        )
    
    # -------------------------------------------------------------------------
    # STEP 4: Extract text content
    # -------------------------------------------------------------------------
    try:
        if file_extension == ".pdf":
            text_content = extract_text_from_pdf(vault_file_path)
        elif file_extension == ".txt":
            text_content = extract_text_from_txt(vault_file_path)
        else:
            # Should never reach here due to validation, but handle it anyway
            text_content = ""
        
        logger.info(f"Text extracted: {len(text_content)} characters")
    
    except Exception as e:
        # If text extraction fails, clean up the saved file
        if vault_file_path.exists():
            vault_file_path.unlink()
        raise
    
    # -------------------------------------------------------------------------
    # STEP 5: Create and save metadata
    # -------------------------------------------------------------------------
    metadata = {
        "document_id": document_id,
        "original_filename": file.filename,
        "file_type": file_extension,
        "upload_timestamp": datetime.utcnow().isoformat(),
        "file_size_bytes": len(content),
        "text_length": len(text_content),
        "vault_path": str(vault_file_path.relative_to(BASE_DIR)),
    }
    
    save_metadata(document_id, metadata)
    
    # -------------------------------------------------------------------------
    # STEP 6: Return response
    # -------------------------------------------------------------------------
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={
            "success": True,
            "message": "Document uploaded successfully",
            "data": {
                "document_id": document_id,
                "filename": file.filename,
                "file_type": file_extension,
                "upload_timestamp": metadata["upload_timestamp"],
                "file_size_bytes": metadata["file_size_bytes"],
                "text_length": metadata["text_length"],
                "text_preview": text_content[:200] + "..." if len(text_content) > 200 else text_content
            }
        }
    )


@router.get("/documents")
async def list_documents():
    """
    List all uploaded documents.
    
    Response:
        - List of document metadata (without full text content)
        
    Academic Note:
    - Simple directory listing using pathlib
    - Returns metadata for all documents in the vault
    - Useful for debugging and demonstration during viva
    """
    
    try:
        # Get all metadata files
        metadata_files = list(METADATA_DIR.glob("*.json"))
        
        documents = []
        for metadata_file in metadata_files:
            try:
                with open(metadata_file, "r", encoding="utf-8") as f:
                    metadata = json.load(f)
                    documents.append(metadata)
            except Exception as e:
                logger.error(f"Error reading metadata file {metadata_file}: {str(e)}")
                continue
        
        # Sort by upload timestamp (newest first)
        documents.sort(key=lambda x: x.get("upload_timestamp", ""), reverse=True)
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "count": len(documents),
                "documents": documents
            }
        )
    
    except Exception as e:
        logger.error(f"Error listing documents: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list documents: {str(e)}"
        )


@router.get("/documents/{document_id}")
async def get_document(document_id: str):
    """
    Retrieve metadata for a specific document.
    
    Args:
        document_id: UUID of the document
        
    Response:
        - Full metadata for the document
        
    Academic Note:
    - Demonstrates path parameter handling in FastAPI
    - Returns 404 if document not found (proper HTTP semantics)
    """
    
    metadata_file = METADATA_DIR / f"{document_id}.json"
    
    if not metadata_file.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID {document_id} not found"
        )
    
    try:
        with open(metadata_file, "r", encoding="utf-8") as f:
            metadata = json.load(f)
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": metadata
            }
        )
    
    except Exception as e:
        logger.error(f"Error reading document metadata: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve document: {str(e)}"
        )


@router.delete("/documents/{document_id}")
async def delete_document(document_id: str):
    """
    Delete a document from the vault and its metadata.
    
    Args:
        document_id: UUID of the document to delete
        
    Response:
        - Confirmation message
        
    Academic Note:
    - Implements proper cleanup (both file and metadata)
    - Demonstrates DELETE method in RESTful API
    """
    
    metadata_file = METADATA_DIR / f"{document_id}.json"
    
    if not metadata_file.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID {document_id} not found"
        )
    
    try:
        # Read metadata to get vault file path
        with open(metadata_file, "r", encoding="utf-8") as f:
            metadata = json.load(f)
        
        # Delete vault file
        vault_file = BASE_DIR / metadata["vault_path"]
        if vault_file.exists():
            vault_file.unlink()
            logger.info(f"Deleted vault file: {vault_file}")
        
        # Delete metadata file
        metadata_file.unlink()
        logger.info(f"Deleted metadata: {metadata_file}")
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "message": f"Document {document_id} deleted successfully"
            }
        )
    
    except Exception as e:
        logger.error(f"Error deleting document: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete document: {str(e)}"
        )