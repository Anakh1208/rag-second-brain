"""
Add these endpoints to app/api/routes/documents.py
These provide delete functionality and document listing
"""

@router.get("/documents/list")
async def list_documents():
    """
    List all uploaded documents.
    
    Returns:
        List of documents with metadata
    
    Example Response:
        {
            "success": true,
            "documents": [
                {
                    "document_id": "abc123...",
                    "filename": "my_notes.pdf",
                    "file_type": ".pdf",
                    "upload_date": "2026-03-01T10:30:00Z",
                    "total_chunks": 15,
                    "file_size_bytes": 245678
                }
            ],
            "total": 1
        }
    """
    from pathlib import Path
    import json
    
    BASE_DIR = Path(__file__).parent.parent.parent.parent
    METADATA_DIR = BASE_DIR / "data" / "metadata"
    
    documents = []
    
    try:
        for meta_file in METADATA_DIR.glob("*.json"):
            try:
                with open(meta_file, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                    
                documents.append({
                    "document_id": meta["document_id"],
                    "filename": meta["original_filename"],
                    "file_type": meta.get("file_type", ""),
                    "upload_date": meta.get("upload_timestamp", ""),
                    "total_chunks": meta.get("total_chunks", 0),
                    "file_size_bytes": meta.get("file_size_bytes", 0)
                })
            except Exception as e:
                logger.warning(f"Error reading metadata file {meta_file.name}: {e}")
                continue
        
        # Sort by upload date (newest first)
        documents.sort(key=lambda x: x.get("upload_date", ""), reverse=True)
        
        return {
            "success": True,
            "documents": documents,
            "total": len(documents)
        }
    
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list documents: {str(e)}"
        )


@router.delete("/documents/{document_id}")
async def delete_document(document_id: str):
    """
    Delete a document from vault and metadata.
    
    WARNING: This does NOT rebuild the index automatically.
    After deleting documents, you should rebuild the index via POST /api/index/build
    
    Args:
        document_id: UUID of the document to delete
    
    Returns:
        {
            "success": true,
            "message": "Document deleted successfully",
            "document_id": "abc123...",
            "reminder": "Please rebuild the index to apply changes"
        }
    """
    import os
    from pathlib import Path
    
    BASE_DIR = Path(__file__).parent.parent.parent.parent
    VAULT_DIR = BASE_DIR / "data" / "vault" / "documents"
    METADATA_DIR = BASE_DIR / "data" / "metadata"
    
    logger.info(f"[Delete] Attempting to delete document: {document_id}")
    
    deleted_files = []
    
    try:
        # Delete metadata file
        metadata_file = METADATA_DIR / f"{document_id}.json"
        if metadata_file.exists():
            os.remove(metadata_file)
            deleted_files.append(str(metadata_file))
            logger.info(f"  ✓ Deleted metadata: {metadata_file.name}")
        else:
            logger.warning(f"  ⚠ Metadata not found: {metadata_file.name}")
        
        # Delete vault file (find by document_id stem)
        vault_file_found = False
        for file in VAULT_DIR.iterdir():
            if file.stem == document_id:
                os.remove(file)
                deleted_files.append(str(file))
                vault_file_found = True
                logger.info(f"  ✓ Deleted vault file: {file.name}")
                break
        
        if not vault_file_found:
            logger.warning(f"  ⚠ Vault file not found for document: {document_id}")
        
        # Check if anything was deleted
        if not deleted_files:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {document_id} not found"
            )
        
        logger.info(f"[Delete] ✅ Successfully deleted document {document_id}")
        
        return {
            "success": True,
            "message": f"Document deleted successfully",
            "document_id": document_id,
            "deleted_files": deleted_files,
            "reminder": "Please rebuild the index to apply changes (POST /api/index/build)"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Delete] ✗ Error deleting document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete document: {str(e)}"
        )


@router.delete("/documents/clear")
async def clear_all_documents():
    """
    DANGER: Delete ALL documents from vault and metadata.
    
    This is useful for testing or starting fresh.
    Use with caution!
    
    Returns:
        {
            "success": true,
            "message": "All documents cleared",
            "total_deleted": 5
        }
    """
    import os
    from pathlib import Path
    
    BASE_DIR = Path(__file__).parent.parent.parent.parent
    VAULT_DIR = BASE_DIR / "data" / "vault" / "documents"
    METADATA_DIR = BASE_DIR / "data" / "metadata"
    
    logger.warning("[Clear All] Deleting ALL documents!")
    
    total_deleted = 0
    
    try:
        # Delete all metadata files
        for meta_file in METADATA_DIR.glob("*.json"):
            os.remove(meta_file)
            total_deleted += 1
        
        # Delete all vault files
        for vault_file in VAULT_DIR.iterdir():
            if vault_file.is_file():
                os.remove(vault_file)
        
        logger.info(f"[Clear All] ✅ Deleted {total_deleted} documents")
        
        return {
            "success": True,
            "message": "All documents cleared",
            "total_deleted": total_deleted,
            "reminder": "You can now upload new documents"
        }
    
    except Exception as e:
        logger.error(f"[Clear All] ✗ Error clearing documents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear documents: {str(e)}"
        )