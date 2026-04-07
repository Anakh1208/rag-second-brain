"""
app/rag/engine.py
-----------------
RAG (Retrieval-Augmented Generation) Retrieval Engine

Academic Note (for SEPM viva):
- Orchestrates the retrieval phase of RAG
- Combines query embedding, vector search, and context construction
- Separates retrieval from generation (modular design)
- Deterministic: same query → same retrieval results

RAG Architecture (Two-Phase):
┌─────────────────────────────────────────────────────────┐
│ PHASE 1: RETRIEVAL (this module)                       │
│ Query → Embedding → FAISS Search → Context             │
└─────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────┐
│ PHASE 2: GENERATION (separate module)                  │
│ Context + Query → LLM → Final Answer                   │
└─────────────────────────────────────────────────────────┘

Why Separate Retrieval and Generation?
1. Modularity: Can swap retrieval or generation independently
2. Testing: Can test retrieval accuracy separately
3. Caching: Can cache retrieval results
4. Transparency: Can inspect what was retrieved before generation
5. Research: Can analyze retrieval quality vs. generation quality
"""

from typing import List, Dict, Optional, Tuple
import logging
from pathlib import Path
import json
import numpy as np

# Import our custom modules
from app.rag.embeddings import generate_query_embedding, EmbeddingModel
from app.rag.vectorstore import FAISSVectorStore
from app.rag.chunker import create_chunks

logger = logging.getLogger(__name__)

# ==============================================================================
# CONFIGURATION
# ==============================================================================

# Paths
BASE_DIR = Path(__file__).parent.parent.parent
METADATA_DIR = BASE_DIR / "data" / "metadata"
VAULT_DIR = BASE_DIR / "data" / "vault" / "documents"

# Default retrieval parameters
DEFAULT_TOP_K = 5
DEFAULT_INDEX_NAME = "default"

# Context formatting
CHUNK_SEPARATOR = "\n" + "=" * 80 + "\n"
CONTEXT_HEADER = "RETRIEVED KNOWLEDGE BASE CONTEXT:\n"

# ==============================================================================
# RAG RETRIEVAL ENGINE
# ==============================================================================

class RAGRetriever:
    """
    RAG Retrieval Engine for semantic search and context construction.
    
    Academic Note (Design Pattern):
    - Facade pattern: Provides simple interface to complex subsystems
    - Hides complexity of embeddings, FAISS, metadata retrieval
    - Single entry point: retrieve_context(query)
    
    Responsibilities:
    1. Query embedding generation
    2. Vector similarity search
    3. Chunk text retrieval from metadata
    4. Context formatting for LLM
    """
    
    def __init__(
        self,
        index_name: str = DEFAULT_INDEX_NAME,
        dimension: int = 384,
        auto_load: bool = True
    ):
        """
        Initialize RAG retriever.
        
        Args:
            index_name: Name of FAISS index to use
            dimension: Embedding dimension (must match model)
            auto_load: Automatically load existing index if available
            
        Academic Note:
        - Lazy loading: Only loads resources when needed
        - Singleton pattern for embedding model (via EmbeddingModel class)
        - Vector store can be shared across requests
        """
        self.index_name = index_name
        self.dimension = dimension
        
        # Initialize vector store
        self.vectorstore = FAISSVectorStore(dimension=dimension)
        
        # Try to load existing index
        if auto_load:
            try:
                self.vectorstore.load_index(index_name)
                logger.info(f"✓ Loaded existing FAISS index: {index_name}")
            except FileNotFoundError:
                logger.info(f"No existing index found: {index_name}")
            except Exception as e:
                logger.warning(f"Could not load index: {str(e)}")
        
        # Initialize embedding model (singleton)
        self.embedding_model = EmbeddingModel()
        
        logger.info("RAG Retriever initialized")
    
    def retrieve_context(
        self,
        query: str,
        top_k: int = DEFAULT_TOP_K,
        include_scores: bool = True
    ) -> Dict:
        """
        Retrieves relevant context for a query (main RAG retrieval function).
        
        Args:
            query: User's search query
            top_k: Number of chunks to retrieve
            include_scores: Include similarity scores in output
            
        Returns:
            Dictionary containing:
                - context_text: Formatted string with all retrieved chunks
                - retrieved_chunks: List of chunk metadata + text
                - query: Original query
                - total_chunks: Number of chunks retrieved
                - avg_similarity: Average similarity score
                
        Academic Note (RAG Retrieval Flow):
        
        Step 1: Query Embedding
        ----------------------
        "What is machine learning?" 
            → [0.23, 0.45, ..., 0.78] (384-dim vector)
        
        Step 2: Vector Search
        --------------------
        FAISS finds top-k most similar chunk embeddings
            → Returns chunk IDs and similarity scores
        
        Step 3: Metadata Retrieval
        --------------------------
        For each chunk ID:
            → Load metadata JSON
            → Extract chunk text, document info
        
        Step 4: Context Construction
        ----------------------------
        Combine chunks into formatted string:
            CHUNK 1 [doc-123, chunk 5] (score: 0.89)
            "Machine learning is a subset of AI..."
            ==========================================
            CHUNK 2 [doc-456, chunk 2] (score: 0.76)
            "Deep learning uses neural networks..."
        
        This context is then passed to LLM for answer generation.
        """
        
        if not query or not query.strip():
            logger.warning("Empty query provided")
            return self._empty_result(query)
        
        logger.info(f"Processing query: {query[:100]}...")
        
        # ---------------------------------------------------------------------
        # STEP 1: Generate query embedding
        # ---------------------------------------------------------------------
        try:
            query_embedding = generate_query_embedding(query)
            logger.info(f"✓ Query embedding generated: {query_embedding.shape}")
        except Exception as e:
            logger.error(f"Failed to generate query embedding: {str(e)}")
            raise RuntimeError(f"Query embedding generation failed: {str(e)}")
        
        # ---------------------------------------------------------------------
        # STEP 2: Search FAISS index
        # ---------------------------------------------------------------------
        try:
            search_results = self.vectorstore.search(query_embedding, top_k=top_k)
            logger.info(f"✓ FAISS search completed: {len(search_results)} results")
        except Exception as e:
            logger.error(f"FAISS search failed: {str(e)}")
            raise RuntimeError(f"Vector search failed: {str(e)}")
        
        if not search_results:
            logger.warning("No results found in FAISS search")
            return self._empty_result(query)
        
        # ---------------------------------------------------------------------
        # STEP 3: Retrieve chunk texts and metadata
        # ---------------------------------------------------------------------
        retrieved_chunks = []
        
        for result in search_results:
            chunk_id = result["chunk_id"]
            document_id = result["document_id"]
            chunk_index = result["chunk_index"]
            similarity_score = result["similarity_score"]
            
            # Load chunk text from metadata
            chunk_text = self._load_chunk_text(chunk_id, document_id)
            
            if chunk_text:
                chunk_data = {
                    "chunk_id": chunk_id,
                    "document_id": document_id,
                    "chunk_index": chunk_index,
                    "chunk_text": chunk_text,
                    "similarity_score": similarity_score,
                    "rank": result["rank"]
                }
                retrieved_chunks.append(chunk_data)
            else:
                logger.warning(f"Could not load text for chunk: {chunk_id}")
        
        logger.info(f"✓ Retrieved {len(retrieved_chunks)} chunks with text")
        
        # ---------------------------------------------------------------------
        # STEP 4: Construct formatted context
        # ---------------------------------------------------------------------
        context_text = self._format_context(retrieved_chunks, include_scores)
        
        # Calculate statistics
        avg_similarity = (
            sum(chunk["similarity_score"] for chunk in retrieved_chunks) / len(retrieved_chunks)
            if retrieved_chunks else 0.0
        )
        
        # ---------------------------------------------------------------------
        # STEP 5: Return complete retrieval result
        # ---------------------------------------------------------------------
        result = {
            "query": query,
            "context_text": context_text,
            "retrieved_chunks": retrieved_chunks,
            "total_chunks": len(retrieved_chunks),
            "avg_similarity": avg_similarity,
            "top_k": top_k
        }
        
        logger.info(f"✓ Retrieval complete: {len(retrieved_chunks)} chunks, "
                   f"avg similarity: {avg_similarity:.4f}")
        
        return result
    
    def _load_chunk_text(self, chunk_id: str, document_id: str) -> Optional[str]:
        """
        Loads chunk text from stored metadata.
        
        Args:
            chunk_id: ID of the chunk
            document_id: ID of the source document
            
        Returns:
            Chunk text if found, None otherwise
            
        Academic Note:
        - Metadata stored as JSON files (one per document)
        - Each metadata file contains document info + all chunks
        - This design allows batch loading of all chunks for a document
        
        Alternative Designs (for discussion):
        1. One JSON per chunk (more granular, slower for batch ops)
        2. Single large JSON (faster loading, harder to update)
        3. Database (more scalable, adds complexity)
        
        We use one JSON per document (good balance for academic prototype)
        """
        
        # First, try to load document metadata
        metadata_file = METADATA_DIR / f"{document_id}.json"
        
        if not metadata_file.exists():
            logger.warning(f"Metadata file not found: {metadata_file}")
            return None
        
        try:
            with open(metadata_file, "r", encoding="utf-8") as f:
                doc_metadata = json.load(f)
            
            # Check if chunk data is stored in metadata
            # (This assumes we store chunks in document metadata)
            # If chunks are stored separately, adjust accordingly
            
            chunks = doc_metadata.get("chunks", [])
            
            for chunk in chunks:
                if chunk.get("chunk_id") == chunk_id:
                    return chunk.get("chunk_text", "")
            
            logger.warning(f"Chunk {chunk_id} not found in document {document_id}")
            return None
            
        except Exception as e:
            logger.error(f"Error loading chunk text: {str(e)}")
            return None
    
    def _format_context(
        self,
        chunks: List[Dict],
        include_scores: bool = True
    ) -> str:
        """
        Formats retrieved chunks into a structured context string.
        
        Args:
            chunks: List of chunk dictionaries
            include_scores: Whether to include similarity scores
            
        Returns:
            Formatted context string ready for LLM
            
        Academic Note (Context Formatting):
        - Clear separation between chunks (visual clarity)
        - Source attribution (document_id, chunk_index)
        - Similarity scores (helpful for debugging)
        - Rank ordering (most relevant first)
        
        Why This Format?
        1. LLM can distinguish between different sources
        2. Human-readable (good for debugging and viva demos)
        3. Maintains provenance (know where info came from)
        4. Easy to modify template for different use cases
        
        Example Output:
        ===============================================
        RETRIEVED KNOWLEDGE BASE CONTEXT:
        ===============================================
        
        [CHUNK 1] Document: doc-123, Position: 5 (Similarity: 0.89)
        Machine learning is a subset of artificial intelligence that enables
        computers to learn from data without being explicitly programmed.
        ===============================================================================
        
        [CHUNK 2] Document: doc-456, Position: 2 (Similarity: 0.76)
        Deep learning is a type of machine learning based on neural networks...
        ===============================================================================
        """
        
        if not chunks:
            return "No relevant context found."
        
        context_parts = [CONTEXT_HEADER]
        context_parts.append("=" * 80)
        context_parts.append("")
        
        for i, chunk in enumerate(chunks, 1):
            # Header with metadata
            header_parts = [f"[CHUNK {i}]"]
            header_parts.append(f"Document: {chunk['document_id']}")
            header_parts.append(f"Position: {chunk['chunk_index']}")
            
            if include_scores:
                header_parts.append(f"(Similarity: {chunk['similarity_score']:.4f})")
            
            header = " ".join(header_parts)
            
            context_parts.append(header)
            context_parts.append(chunk["chunk_text"])
            context_parts.append(CHUNK_SEPARATOR)
        
        return "\n".join(context_parts)
    
    def _empty_result(self, query: str) -> Dict:
        """
        Returns empty result structure when no results found.
        
        Args:
            query: Original query
            
        Returns:
            Empty result dictionary
        """
        return {
            "query": query,
            "context_text": "No relevant context found.",
            "retrieved_chunks": [],
            "total_chunks": 0,
            "avg_similarity": 0.0,
            "top_k": 0
        }
    
    def get_stats(self) -> Dict:
        """
        Returns statistics about the retriever.
        
        Returns:
            Dictionary with retriever statistics
            
        Academic Note:
        - Useful for monitoring and debugging
        - Can expose via API endpoint
        - Shows index health and readiness
        """
        vectorstore_stats = self.vectorstore.get_stats()
        
        return {
            "index_name": self.index_name,
            "dimension": self.dimension,
            "vectorstore": vectorstore_stats,
            "status": "ready" if vectorstore_stats["total_vectors"] > 0 else "empty"
        }


# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def retrieve_for_query(
    query: str,
    top_k: int = DEFAULT_TOP_K,
    index_name: str = DEFAULT_INDEX_NAME
) -> Dict:
    """
    Convenience function for one-off retrievals.
    
    Args:
        query: User query
        top_k: Number of chunks to retrieve
        index_name: Name of FAISS index
        
    Returns:
        Retrieval result dictionary
        
    Academic Note:
    - Functional wrapper around class-based retriever
    - Creates new retriever instance each time
    - Useful for simple scripts or testing
    - For production, reuse RAGRetriever instance (more efficient)
    """
    retriever = RAGRetriever(index_name=index_name, auto_load=True)
    return retriever.retrieve_context(query, top_k=top_k)


# ==============================================================================
# EXAMPLE USAGE (for testing)
# ==============================================================================
if __name__ == "__main__":
    print("=" * 80)
    print("RAG RETRIEVAL ENGINE TEST")
    print("=" * 80)
    
    # Note: This test requires:
    # 1. Documents to be uploaded
    # 2. Embeddings to be generated
    # 3. FAISS index to be built
    
    try:
        # Initialize retriever
        print("\n[Test 1] Initializing RAG retriever...")
        retriever = RAGRetriever(auto_load=True)
        
        # Get stats
        stats = retriever.get_stats()
        print(f"\nRetriever stats:")
        print(f"  Status: {stats['status']}")
        print(f"  Index: {stats['index_name']}")
        print(f"  Total vectors: {stats['vectorstore']['total_vectors']}")
        
        if stats['vectorstore']['total_vectors'] == 0:
            print("\n⚠ No vectors in index. Please:")
            print("  1. Upload documents via /api/documents/upload")
            print("  2. Build index (to be implemented)")
            print("  3. Then retry this test")
        else:
            # Test retrieval
            print("\n[Test 2] Testing retrieval...")
            
            test_queries = [
                "What is machine learning?",
                "How does deep learning work?",
                "Explain natural language processing"
            ]
            
            for query in test_queries:
                print(f"\n{'=' * 80}")
                print(f"Query: {query}")
                print(f"{'=' * 80}")
                
                result = retriever.retrieve_context(query, top_k=3)
                
                print(f"\nRetrieved {result['total_chunks']} chunks")
                print(f"Average similarity: {result['avg_similarity']:.4f}")
                
                print("\nContext Preview (first 300 chars):")
                print(result['context_text'][:300] + "...")
                
                print("\nRetrieved Chunks Summary:")
                for chunk in result['retrieved_chunks']:
                    print(f"  - {chunk['document_id']} [chunk {chunk['chunk_index']}] "
                          f"(score: {chunk['similarity_score']:.4f})")
        
        print("\n" + "=" * 80)
        print("✓ RAG Retrieval Engine test completed!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n✗ Test failed: {str(e)}")
        logger.exception("Test failed")
