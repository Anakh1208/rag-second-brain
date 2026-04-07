"""
app/api/routes/index.py
-----------------------
Index Building and Management API Routes

Handles the indexing pipeline:
1. Read uploaded documents
2. Chunk text
3. Generate embeddings
4. Build FAISS index
"""

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from pathlib import Path
import json
import logging
from typing import List, Dict

from app.rag.chunker import create_chunks
from app.rag.embeddings import generate_embeddings
from app.rag.vectorstore import FAISSVectorStore

logger = logging.getLogger(__name__)

router = APIRouter()

# Paths
BASE_DIR = Path(__file__).parent.parent.parent.parent
METADATA_DIR = BASE_DIR / "data" / "metadata"
VAULT_DIR = BASE_DIR / "data" / "vault" / "documents"

# ==============================================================================
# INDEX BUILDING ENDPOINT
# ==============================================================================

@router.post("/index/build")
async def build_index():
    """
    Builds FAISS index from all uploaded documents.
    
    Process:
    1. Load all document metadata
    2. Chunk each document
    3. Generate embeddings for all chunks
    4. Build FAISS index
    5. Save index to disk
    
    Returns:
        Summary of indexing process
    """
    
    logger.info("=" * 80)
    logger.info("BUILDING FAISS INDEX")
    logger.info("=" * 80)
    
    # -------------------------------------------------------------------------
    # STEP 1: Load all documents
    # -------------------------------------------------------------------------
    logger.info("\n[STEP 1] Loading documents...")
    
    metadata_files = list(METADATA_DIR.glob("*.json"))
    
    if not metadata_files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No documents found. Please upload documents first."
        )
    
    logger.info(f"Found {len(metadata_files)} documents")
    
    # -------------------------------------------------------------------------
    # STEP 2: Chunk all documents
    # -------------------------------------------------------------------------
    logger.info("\n[STEP 2] Chunking documents...")
    
    all_chunks = []
    documents_processed = 0
    
    for metadata_file in metadata_files:
        try:
            with open(metadata_file, "r", encoding="utf-8") as f:
                doc_metadata = json.load(f)
            
            document_id = doc_metadata["document_id"]
            vault_path = BASE_DIR / doc_metadata["vault_path"]
            
            # Read document text
            if vault_path.suffix.lower() == ".txt":
                with open(vault_path, "r", encoding="utf-8") as f:
                    text = f.read()
            elif vault_path.suffix.lower() == ".pdf":
                from PyPDF2 import PdfReader
                reader = PdfReader(str(vault_path))
                text = "\n".join([page.extract_text() for page in reader.pages])
            else:
                logger.warning(f"Unsupported file type: {vault_path}")
                continue
            
            # Create chunks
            chunks = create_chunks(
                text=text,
                document_id=document_id,
                chunk_size=500,
                overlap=100
            )
            
            all_chunks.extend(chunks)
            documents_processed += 1
            
            logger.info(f"  ✓ {doc_metadata['original_filename']}: {len(chunks)} chunks")
            
        except Exception as e:
            logger.error(f"Error processing {metadata_file}: {str(e)}")
            continue
    
    if not all_chunks:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No chunks created from documents"
        )
    
    logger.info(f"\n✓ Total chunks created: {len(all_chunks)}")
    
    # -------------------------------------------------------------------------
    # STEP 3: Generate embeddings
    # -------------------------------------------------------------------------
    logger.info("\n[STEP 3] Generating embeddings...")
    
    try:
        embedding_records = generate_embeddings(all_chunks)
        logger.info(f"✓ Generated {len(embedding_records)} embeddings")
    except Exception as e:
        logger.error(f"Embedding generation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate embeddings: {str(e)}"
        )
    
    # -------------------------------------------------------------------------
    # STEP 4: Build FAISS index
    # -------------------------------------------------------------------------
    logger.info("\n[STEP 4] Building FAISS index...")
    
    try:
        vectorstore = FAISSVectorStore(dimension=384)
        vectorstore.build_index(embedding_records)
        logger.info(f"✓ FAISS index built: {vectorstore.index.ntotal} vectors")
    except Exception as e:
        logger.error(f"Index building failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to build index: {str(e)}"
        )
    
    # -------------------------------------------------------------------------
    # STEP 5: Save chunks to metadata (for retrieval)
    # -------------------------------------------------------------------------
    logger.info("\n[STEP 5] Saving chunk metadata...")
    
    # Group chunks by document
    chunks_by_doc = {}
    for chunk in all_chunks:
        doc_id = chunk["document_id"]
        if doc_id not in chunks_by_doc:
            chunks_by_doc[doc_id] = []
        chunks_by_doc[doc_id].append(chunk)
    
    # Update each document's metadata with chunks
    for doc_id, chunks in chunks_by_doc.items():
        metadata_file = METADATA_DIR / f"{doc_id}.json"
        
        try:
            with open(metadata_file, "r", encoding="utf-8") as f:
                doc_metadata = json.load(f)
            
            doc_metadata["chunks"] = chunks
            doc_metadata["total_chunks"] = len(chunks)
            
            with open(metadata_file, "w", encoding="utf-8") as f:
                json.dump(doc_metadata, f, indent=2)
            
        except Exception as e:
            logger.error(f"Failed to update metadata for {doc_id}: {str(e)}")
    
    logger.info(f"✓ Chunk metadata saved")
    
    # -------------------------------------------------------------------------
    # STEP 6: Save FAISS index to disk
    # -------------------------------------------------------------------------
    logger.info("\n[STEP 6] Saving FAISS index to disk...")
    
    try:
        vectorstore.save_index("default")
        logger.info("✓ Index saved successfully")
    except Exception as e:
        logger.error(f"Index saving failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save index: {str(e)}"
        )
    
    # -------------------------------------------------------------------------
    # Return summary
    # -------------------------------------------------------------------------
    logger.info("\n" + "=" * 80)
    logger.info("INDEX BUILDING COMPLETE")
    logger.info("=" * 80 + "\n")
    
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "success": True,
            "message": "FAISS index built successfully",
            "summary": {
                "documents_processed": documents_processed,
                "total_chunks": len(all_chunks),
                "total_embeddings": len(embedding_records),
                "index_size": vectorstore.index.ntotal,
                "dimension": vectorstore.dimension
            }
        }
    )


@router.get("/index/status")
async def index_status():
    """
    Returns current index status.
    """
    
    try:
        vectorstore = FAISSVectorStore(dimension=384)
        vectorstore.load_index("default")
        
        stats = vectorstore.get_stats()
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "ready" if stats["total_vectors"] > 0 else "empty",
                "total_vectors": stats["total_vectors"],
                "dimension": stats["dimension"]
            }
        )
    
    except FileNotFoundError:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "not_built",
                "total_vectors": 0,
                "message": "Index not built yet. Call POST /api/index/build"
            }
        )