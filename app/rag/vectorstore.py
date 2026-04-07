"""
app/rag/vectorstore.py
----------------------
FAISS Vector Store Module for RAG Pipeline

Academic Note (for SEPM viva):
- FAISS (Facebook AI Similarity Search) enables fast nearest neighbor search
- Uses IndexFlatIP (Inner Product) for cosine similarity search
- Stores embeddings in-memory for fast retrieval
- Maintains mapping between FAISS index positions and chunk metadata
- Persistence: saves/loads index to/from disk

Why FAISS?
1. Optimized for high-dimensional vector similarity search
2. Much faster than brute-force comparison (especially for large datasets)
3. Supports various index types (Flat, IVF, HNSW, etc.)
4. Industry standard for vector databases
5. Works well on CPU (GPU support also available)

How RAG Uses FAISS:
1. Build index: Add all chunk embeddings to FAISS
2. Query time: Convert query to embedding
3. Search: FAISS finds top-k most similar chunks
4. Retrieve: Return corresponding chunk metadata and text
5. Generate: LLM uses retrieved chunks to generate answer
"""

import faiss
import numpy as np
import pickle
import json
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

# ==============================================================================
# CONFIGURATION
# ==============================================================================

# Directory for storing FAISS indices
BASE_DIR = Path(__file__).parent.parent.parent
INDEX_DIR = BASE_DIR / "data" / "faiss_index"
INDEX_DIR.mkdir(parents=True, exist_ok=True)

# Default file names
INDEX_FILE = "vector.index"
METADATA_FILE = "metadata.pkl"
CONFIG_FILE = "config.json"

# ==============================================================================
# FAISS VECTOR STORE CLASS
# ==============================================================================

class FAISSVectorStore:
    """
    FAISS-based vector store for semantic search in RAG pipeline.
    
    Academic Note (Design Decisions):
    - Uses IndexFlatIP (Inner Product) for exact cosine similarity
    - Flat index = brute-force search (100% accuracy, good for small datasets)
    - For larger datasets, could use IndexIVFFlat or IndexHNSW (approximate search)
    - Maintains separate metadata storage (FAISS only stores vectors)
    
    Data Structure:
    - FAISS index: Stores embeddings at positions 0, 1, 2, ...
    - Metadata list: chunk_metadata[i] corresponds to embedding at position i
    - This mapping enables retrieval of original chunk data
    
    Index Types Comparison (for viva discussion):
    - IndexFlatIP: Exact search, O(n) time, 100% recall
    - IndexIVFFlat: Approximate, faster, ~95% recall (for large datasets)
    - IndexHNSW: Graph-based, very fast, ~98% recall
    
    We use IndexFlatIP for academic clarity and dataset size (<10k chunks)
    """
    
    def __init__(self, dimension: int = 384):
        """
        Initialize FAISS vector store.
        
        Args:
            dimension: Embedding dimension (384 for all-MiniLM-L6-v2)
            
        Academic Note:
        - Dimension must match embedding model output
        - all-MiniLM-L6-v2 produces 384-dimensional embeddings
        - Mismatch will cause runtime errors
        """
        self.dimension = dimension
        self.index = None
        self.metadata = []  # List storing chunk metadata
        self.config = {
            "dimension": dimension,
            "index_type": "IndexFlatIP",
            "total_vectors": 0
        }
        
        logger.info(f"Initialized FAISSVectorStore with dimension={dimension}")
    
    def build_index(self, embedding_records: List[Dict]) -> None:
        """
        Builds FAISS index from embedding records.
        
        Args:
            embedding_records: List of dicts containing:
                - chunk_id: Unique chunk identifier
                - document_id: Source document ID
                - chunk_index: Position in document
                - embedding: List of floats (384-dim vector)
                
        Academic Note (Index Building Process):
        1. Extract embeddings as numpy array (n × 384)
        2. Extract metadata (chunk_id, document_id, etc.)
        3. Create FAISS IndexFlatIP (inner product = cosine for normalized vectors)
        4. Add embeddings to index (FAISS assigns positions 0, 1, 2, ...)
        5. Store metadata in same order
        
        Why IndexFlatIP?
        - IP = Inner Product
        - For normalized vectors: dot(A, B) = cosine_similarity(A, B)
        - Exact search (no approximation)
        - Simple and deterministic (good for academic prototype)
        
        Time Complexity:
        - Building: O(n) where n = number of embeddings
        - Searching: O(n × d) where d = dimension (brute-force)
        """
        
        if not embedding_records:
            logger.warning("No embedding records provided for index building")
            return
        
        logger.info(f"Building FAISS index from {len(embedding_records)} embeddings")
        
        # ---------------------------------------------------------------------
        # STEP 1: Extract embeddings as numpy array
        # ---------------------------------------------------------------------
        embeddings_list = []
        metadata_list = []
        
        for record in embedding_records:
            # Validate record structure
            if "embedding" not in record:
                logger.warning(f"Record missing embedding: {record.get('chunk_id', 'unknown')}")
                continue
            
            embedding = record["embedding"]
            
            # Ensure embedding is correct dimension
            if len(embedding) != self.dimension:
                logger.warning(
                    f"Embedding dimension mismatch: expected {self.dimension}, "
                    f"got {len(embedding)} for chunk {record.get('chunk_id', 'unknown')}"
                )
                continue
            
            embeddings_list.append(embedding)
            
            # Store metadata (everything except the embedding vector)
            metadata_list.append({
                "chunk_id": record.get("chunk_id"),
                "document_id": record.get("document_id"),
                "chunk_index": record.get("chunk_index")
            })
        
        if not embeddings_list:
            logger.error("No valid embeddings found in records")
            return
        
        # Convert to numpy array (required by FAISS)
        embeddings_array = np.array(embeddings_list, dtype=np.float32)
        
        logger.info(f"Embeddings array shape: {embeddings_array.shape}")
        
        # ---------------------------------------------------------------------
        # STEP 2: Create FAISS index
        # ---------------------------------------------------------------------
        # IndexFlatIP: Flat (brute-force) index using Inner Product similarity
        # For normalized embeddings, inner product = cosine similarity
        self.index = faiss.IndexFlatIP(self.dimension)
        
        logger.info(f"Created FAISS index: {self.index.__class__.__name__}")
        
        # ---------------------------------------------------------------------
        # STEP 3: Add embeddings to index
        # ---------------------------------------------------------------------
        self.index.add(embeddings_array)
        
        # Store metadata in same order
        self.metadata = metadata_list
        
        # Update config
        self.config["total_vectors"] = len(embeddings_list)
        
        logger.info(f"✓ FAISS index built successfully")
        logger.info(f"  Total vectors: {self.index.ntotal}")
        logger.info(f"  Dimension: {self.dimension}")
        logger.info(f"  Index type: {self.config['index_type']}")
    
    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 5
    ) -> List[Dict]:
        """
        Searches for most similar vectors in the index.
        
        Args:
            query_embedding: Query vector (384-dim numpy array)
            top_k: Number of results to return
            
        Returns:
            List of dicts containing:
                - chunk_id: ID of retrieved chunk
                - document_id: Source document
                - chunk_index: Position in document
                - similarity_score: Cosine similarity (0 to 1)
                - rank: Position in results (0 = most similar)
                
        Academic Note (Search Process):
        1. FAISS compares query against all stored vectors
        2. Calculates inner product (= cosine for normalized vectors)
        3. Returns top-k highest scores with their positions
        4. We map positions back to metadata
        
        FAISS Search Output:
        - distances: Array of similarity scores [shape: (1, k)]
        - indices: Array of positions in index [shape: (1, k)]
        
        Example:
        Query: "What is machine learning?"
        FAISS returns: indices=[42, 17, 89], distances=[0.89, 0.76, 0.65]
        We retrieve: metadata[42], metadata[17], metadata[89]
        """
        
        if self.index is None:
            raise RuntimeError("Index not built. Call build_index() first.")
        
        if self.index.ntotal == 0:
            logger.warning("Index is empty, no results to return")
            return []
        
        # Ensure query is correct shape and type
        if not isinstance(query_embedding, np.ndarray):
            query_embedding = np.array(query_embedding, dtype=np.float32)
        
        if query_embedding.dtype != np.float32:
            query_embedding = query_embedding.astype(np.float32)
        
        # FAISS expects 2D array: (num_queries, dimension)
        if len(query_embedding.shape) == 1:
            query_embedding = query_embedding.reshape(1, -1)
        
        # Validate dimension
        if query_embedding.shape[1] != self.dimension:
            raise ValueError(
                f"Query dimension {query_embedding.shape[1]} "
                f"does not match index dimension {self.dimension}"
            )
        
        # Limit top_k to available vectors
        k = min(top_k, self.index.ntotal)
        
        logger.info(f"Searching FAISS index for top {k} results")
        
        # ---------------------------------------------------------------------
        # STEP 1: Search FAISS index
        # ---------------------------------------------------------------------
        # search() returns (distances, indices)
        # distances: similarity scores (higher = more similar)
        # indices: positions in the index
        distances, indices = self.index.search(query_embedding, k)
        
        # ---------------------------------------------------------------------
        # STEP 2: Map indices to metadata
        # ---------------------------------------------------------------------
        results = []
        
        # indices and distances are 2D arrays (batch support)
        # We only have 1 query, so take first row
        for rank, (idx, score) in enumerate(zip(indices[0], distances[0])):
            # idx is the position in FAISS index
            # score is the similarity (inner product / cosine)
            
            # Retrieve corresponding metadata
            if 0 <= idx < len(self.metadata):
                result = {
                    **self.metadata[idx],  # Include chunk_id, document_id, chunk_index
                    "similarity_score": float(score),
                    "rank": rank,
                    "faiss_index": int(idx)
                }
                results.append(result)
            else:
                logger.warning(f"Invalid index returned by FAISS: {idx}")
        
        logger.info(f"✓ Found {len(results)} results")
        
        return results
    
    def save_index(self, index_name: str = "default") -> None:
        """
        Saves FAISS index and metadata to disk.
        
        Args:
            index_name: Name for the index (allows multiple indices)
            
        Academic Note (Persistence):
        - FAISS index saved as binary file (optimized format)
        - Metadata saved as pickle (Python object serialization)
        - Config saved as JSON (human-readable)
        
        File Structure:
        data/faiss_index/
        ├── default_vector.index    (FAISS binary)
        ├── default_metadata.pkl    (Python pickle)
        └── default_config.json     (JSON config)
        
        Why Three Files?
        - Index: FAISS-specific binary format (efficient)
        - Metadata: Python objects (chunk_id, document_id, etc.)
        - Config: Human-readable settings (dimension, count, etc.)
        """
        
        if self.index is None:
            raise RuntimeError("No index to save. Build index first.")
        
        logger.info(f"Saving FAISS index: {index_name}")
        
        # Define file paths
        index_path = INDEX_DIR / f"{index_name}_{INDEX_FILE}"
        metadata_path = INDEX_DIR / f"{index_name}_{METADATA_FILE}"
        config_path = INDEX_DIR / f"{index_name}_{CONFIG_FILE}"
        
        try:
            # Save FAISS index
            faiss.write_index(self.index, str(index_path))
            logger.info(f"✓ Saved FAISS index: {index_path}")
            
            # Save metadata
            with open(metadata_path, "wb") as f:
                pickle.dump(self.metadata, f)
            logger.info(f"✓ Saved metadata: {metadata_path}")
            
            # Save config
            with open(config_path, "w") as f:
                json.dump(self.config, f, indent=2)
            logger.info(f"✓ Saved config: {config_path}")
            
            logger.info(f"✓ Index saved successfully: {index_name}")
            
        except Exception as e:
            logger.error(f"Error saving index: {str(e)}")
            raise RuntimeError(f"Failed to save index: {str(e)}")
    
    def load_index(self, index_name: str = "default") -> None:
        """
        Loads FAISS index and metadata from disk.
        
        Args:
            index_name: Name of the index to load
            
        Academic Note:
        - Restores previously built index
        - Enables persistence across application restarts
        - Much faster than rebuilding (no embedding generation needed)
        
        Use Case:
        - App starts → load existing index
        - New document uploaded → rebuild index
        - Query comes in → use loaded index
        """
        
        # Define file paths
        index_path = INDEX_DIR / f"{index_name}_{INDEX_FILE}"
        metadata_path = INDEX_DIR / f"{index_name}_{METADATA_FILE}"
        config_path = INDEX_DIR / f"{index_name}_{CONFIG_FILE}"
        
        # Check if files exist
        if not index_path.exists():
            raise FileNotFoundError(f"Index file not found: {index_path}")
        if not metadata_path.exists():
            raise FileNotFoundError(f"Metadata file not found: {metadata_path}")
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        
        logger.info(f"Loading FAISS index: {index_name}")
        
        try:
            # Load FAISS index
            self.index = faiss.read_index(str(index_path))
            logger.info(f"✓ Loaded FAISS index: {index_path}")
            
            # Load metadata
            with open(metadata_path, "rb") as f:
                self.metadata = pickle.load(f)
            logger.info(f"✓ Loaded metadata: {len(self.metadata)} records")
            
            # Load config
            with open(config_path, "r") as f:
                self.config = json.load(f)
            logger.info(f"✓ Loaded config: {config_path}")
            
            # Validate consistency
            if self.index.ntotal != len(self.metadata):
                logger.warning(
                    f"Inconsistency: index has {self.index.ntotal} vectors "
                    f"but metadata has {len(self.metadata)} records"
                )
            
            logger.info(f"✓ Index loaded successfully")
            logger.info(f"  Total vectors: {self.index.ntotal}")
            logger.info(f"  Dimension: {self.dimension}")
            
        except Exception as e:
            logger.error(f"Error loading index: {str(e)}")
            raise RuntimeError(f"Failed to load index: {str(e)}")
    
    def delete_index(self, index_name: str = "default") -> None:
        """
        Deletes saved index files from disk.
        
        Args:
            index_name: Name of the index to delete
            
        Academic Note:
        - Cleanup operation (useful for testing)
        - Removes all three files (index, metadata, config)
        """
        
        index_path = INDEX_DIR / f"{index_name}_{INDEX_FILE}"
        metadata_path = INDEX_DIR / f"{index_name}_{METADATA_FILE}"
        config_path = INDEX_DIR / f"{index_name}_{CONFIG_FILE}"
        
        deleted_files = []
        
        for path in [index_path, metadata_path, config_path]:
            if path.exists():
                path.unlink()
                deleted_files.append(path.name)
        
        if deleted_files:
            logger.info(f"✓ Deleted index files: {', '.join(deleted_files)}")
        else:
            logger.warning(f"No files found for index: {index_name}")
    
    def get_stats(self) -> Dict:
        """
        Returns statistics about the vector store.
        
        Returns:
            Dictionary with index statistics
            
        Academic Note:
        - Useful for debugging and monitoring
        - Can be exposed via API endpoint
        """
        
        if self.index is None:
            return {
                "status": "not_initialized",
                "total_vectors": 0,
                "dimension": self.dimension
            }
        
        return {
            "status": "ready",
            "total_vectors": self.index.ntotal,
            "dimension": self.dimension,
            "index_type": self.config["index_type"],
            "metadata_count": len(self.metadata)
        }


# ==============================================================================
# EXAMPLE USAGE (for testing)
# ==============================================================================
if __name__ == "__main__":
    print("=" * 60)
    print("FAISS VECTOR STORE TEST")
    print("=" * 60)
    
    # Sample embedding records (as would come from embeddings.py)
    sample_records = [
        {
            "chunk_id": "chunk-001",
            "document_id": "doc-123",
            "chunk_index": 0,
            "embedding": np.random.randn(384).tolist()  # Random for testing
        },
        {
            "chunk_id": "chunk-002",
            "document_id": "doc-123",
            "chunk_index": 1,
            "embedding": np.random.randn(384).tolist()
        },
        {
            "chunk_id": "chunk-003",
            "document_id": "doc-456",
            "chunk_index": 0,
            "embedding": np.random.randn(384).tolist()
        }
    ]
    
    # -------------------------------------------------------------------------
    # Test 1: Build index
    # -------------------------------------------------------------------------
    print("\n[Test 1] Building FAISS index...")
    
    vectorstore = FAISSVectorStore(dimension=384)
    vectorstore.build_index(sample_records)
    
    stats = vectorstore.get_stats()
    print(f"Index stats: {stats}")
    
    # -------------------------------------------------------------------------
    # Test 2: Search
    # -------------------------------------------------------------------------
    print("\n[Test 2] Searching index...")
    
    # Create random query embedding
    query_embedding = np.random.randn(384).astype(np.float32)
    
    results = vectorstore.search(query_embedding, top_k=2)
    
    print(f"Found {len(results)} results:")
    for result in results:
        print(f"  Rank {result['rank']}: chunk={result['chunk_id']}, "
              f"score={result['similarity_score']:.4f}")
    
    # -------------------------------------------------------------------------
    # Test 3: Save and load
    # -------------------------------------------------------------------------
    print("\n[Test 3] Saving index...")
    vectorstore.save_index("test_index")
    
    print("\n[Test 4] Loading index...")
    new_vectorstore = FAISSVectorStore(dimension=384)
    new_vectorstore.load_index("test_index")
    
    new_stats = new_vectorstore.get_stats()
    print(f"Loaded index stats: {new_stats}")
    
    # Search with loaded index
    new_results = new_vectorstore.search(query_embedding, top_k=2)
    print(f"Search after loading: {len(new_results)} results")
    
    # -------------------------------------------------------------------------
    # Test 5: Cleanup
    # -------------------------------------------------------------------------
    print("\n[Test 5] Cleaning up...")
    vectorstore.delete_index("test_index")
    
    print("\n" + "=" * 60)
    print("✓ All tests completed successfully!")
    print("=" * 60)