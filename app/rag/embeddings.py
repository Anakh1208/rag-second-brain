"""
app/rag/embeddings.py
---------------------
Embedding Generation Module for RAG Pipeline

Academic Note (for SEPM viva):
- Converts text chunks into dense vector representations (embeddings)
- Uses sentence-transformers library (built on top of HuggingFace transformers)
- Model: all-MiniLM-L6-v2 (384-dimensional embeddings)
- Embeddings capture semantic meaning, enabling similarity search
- Singleton pattern ensures model is loaded only once (memory efficiency)

Why Embeddings are Critical for RAG:
1. Enable semantic search (not just keyword matching)
2. Similar concepts have similar embeddings (cosine similarity)
3. Foundation for vector databases (FAISS, Pinecone, etc.)
4. Allow retrieval based on meaning, not exact text matches

Example:
"What is AI?" and "Explain artificial intelligence" will have similar embeddings
even though they share no common words (except "intelligence" → "AI")
"""

from sentence_transformers import SentenceTransformer
from typing import List, Dict
import numpy as np
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# ==============================================================================
# CONFIGURATION
# ==============================================================================

# Model selection
# all-MiniLM-L6-v2: Small, fast, 384-dimensional embeddings
# Good balance between speed and quality for academic prototype
MODEL_NAME = "all-MiniLM-L6-v2"

# Cache directory for model files (avoids re-downloading)
CACHE_DIR = Path(__file__).parent.parent.parent / "data" / "model_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# ==============================================================================
# SINGLETON MODEL LOADER
# ==============================================================================

class EmbeddingModel:
    """
    Singleton class to manage the sentence-transformer model.
    
    Academic Note (Design Pattern):
    - Implements Singleton pattern to ensure only one model instance
    - Model loading is expensive (memory + time)
    - Reusing the same instance improves efficiency
    - Thread-safe for FastAPI concurrent requests
    
    Why Singleton?
    - Model is ~80MB in memory
    - Loading takes ~2-5 seconds
    - Multiple instances waste resources
    - Single instance serves all embedding requests
    """
    
    _instance = None
    _model = None
    
    def __new__(cls):
        """
        Ensures only one instance of EmbeddingModel exists.
        
        Academic Note:
        - __new__ is called before __init__
        - Returns existing instance if already created
        - Classic singleton implementation in Python
        """
        if cls._instance is None:
            cls._instance = super(EmbeddingModel, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """
        Initializes the model (only once due to singleton).
        """
        if EmbeddingModel._model is None:
            logger.info(f"Loading embedding model: {MODEL_NAME}")
            logger.info(f"Cache directory: {CACHE_DIR}")
            
            try:
                # Load the pre-trained model
                # First run will download ~80MB, subsequent runs use cache
                EmbeddingModel._model = SentenceTransformer(
                    MODEL_NAME,
                    cache_folder=str(CACHE_DIR)
                )
                
                logger.info(f"✓ Model loaded successfully")
                logger.info(f"  Embedding dimension: {self.get_embedding_dimension()}")
                
            except Exception as e:
                logger.error(f"Failed to load embedding model: {str(e)}")
                raise RuntimeError(f"Could not load model {MODEL_NAME}: {str(e)}")
    
    def get_model(self) -> SentenceTransformer:
        """
        Returns the loaded model instance.
        
        Returns:
            SentenceTransformer model
        """
        return EmbeddingModel._model
    
    def get_embedding_dimension(self) -> int:
        """
        Returns the dimensionality of the embeddings.
        
        Returns:
            Integer representing embedding dimension (384 for all-MiniLM-L6-v2)
            
        Academic Note:
        - all-MiniLM-L6-v2 produces 384-dimensional vectors
        - Higher dimensions = more information capacity
        - Trade-off: dimension vs. storage/computation cost
        """
        if EmbeddingModel._model is None:
            return 0
        return EmbeddingModel._model.get_sentence_embedding_dimension()


# ==============================================================================
# EMBEDDING GENERATION FUNCTIONS
# ==============================================================================

def generate_embeddings(chunks: List[Dict]) -> List[Dict]:
    """
    Generates embeddings for a list of text chunks.
    
    Args:
        chunks: List of chunk dictionaries, each containing:
            - chunk_id: Unique identifier
            - document_id: Source document ID
            - chunk_text: Text content to embed
            - chunk_index: Position in document
            
    Returns:
        List of dictionaries containing:
            - chunk_id: Original chunk ID
            - document_id: Original document ID
            - chunk_index: Original chunk index
            - embedding: List of floats (384-dimensional vector)
            - embedding_dimension: Size of the embedding vector
            
    Academic Note (Embedding Process):
    1. Extract text from each chunk
    2. Pass text through transformer model
    3. Model outputs dense vector representation
    4. Vector captures semantic meaning of text
    5. Similar texts have similar vectors (measured by cosine similarity)
    
    How Transformers Work (Simplified):
    - Text → Tokenization → Attention Mechanism → Pooling → Vector
    - "Attention" allows model to focus on important words
    - Final vector is a compressed semantic representation
    
    Example:
    Input: "Machine learning is a subset of AI"
    Output: [0.123, -0.456, 0.789, ..., 0.234] (384 numbers)
    """
    
    if not chunks:
        logger.warning("No chunks provided for embedding generation")
        return []
    
    # -------------------------------------------------------------------------
    # STEP 1: Initialize model (singleton pattern)
    # -------------------------------------------------------------------------
    embedding_model = EmbeddingModel()
    model = embedding_model.get_model()
    
    logger.info(f"Generating embeddings for {len(chunks)} chunks")
    
    # -------------------------------------------------------------------------
    # STEP 2: Extract text from chunks
    # -------------------------------------------------------------------------
    texts = []
    chunk_metadata = []
    
    for chunk in chunks:
        # Validate chunk structure
        if "chunk_text" not in chunk:
            logger.warning(f"Chunk missing 'chunk_text' field: {chunk.get('chunk_id', 'unknown')}")
            continue
        
        texts.append(chunk["chunk_text"])
        chunk_metadata.append({
            "chunk_id": chunk.get("chunk_id"),
            "document_id": chunk.get("document_id"),
            "chunk_index": chunk.get("chunk_index")
        })
    
    if not texts:
        logger.error("No valid texts found in chunks")
        return []
    
    # -------------------------------------------------------------------------
    # STEP 3: Generate embeddings using the model
    # -------------------------------------------------------------------------
    try:
        # encode() returns a numpy array of shape (num_texts, embedding_dim)
        # Each row is the embedding for one text chunk
        embeddings_array = model.encode(
            texts,
            convert_to_numpy=True,  # Return as numpy array (not torch tensor)
            show_progress_bar=False,  # Disable progress bar (cleaner logs)
            normalize_embeddings=True  # Normalize to unit length (better for cosine similarity)
        )
        
        logger.info(f"✓ Generated embeddings: shape={embeddings_array.shape}")
        
    except Exception as e:
        logger.error(f"Error generating embeddings: {str(e)}")
        raise RuntimeError(f"Failed to generate embeddings: {str(e)}")
    
    # -------------------------------------------------------------------------
    # STEP 4: Combine embeddings with metadata
    # -------------------------------------------------------------------------
    results = []
    
    for idx, (metadata, embedding_vector) in enumerate(zip(chunk_metadata, embeddings_array)):
        result = {
            "chunk_id": metadata["chunk_id"],
            "document_id": metadata["document_id"],
            "chunk_index": metadata["chunk_index"],
            "embedding": embedding_vector.tolist(),  # Convert numpy array to list
            "embedding_dimension": len(embedding_vector)
        }
        results.append(result)
    
    logger.info(f"✓ Created {len(results)} embedding records")
    
    return results


def generate_query_embedding(query_text: str) -> np.ndarray:
    """
    Generates an embedding for a search query.
    
    Args:
        query_text: User's search query
        
    Returns:
        Numpy array containing the query embedding
        
    Academic Note:
    - Query and document chunks use the SAME model
    - This ensures embeddings are in the same vector space
    - Enables meaningful similarity comparisons
    - Query embedding will be compared against chunk embeddings in FAISS
    
    Example Usage in RAG:
    1. User asks: "What is machine learning?"
    2. Generate query embedding
    3. Find top-k most similar chunk embeddings
    4. Return corresponding chunks to LLM
    5. LLM generates answer using retrieved chunks
    """
    
    if not query_text or not query_text.strip():
        raise ValueError("Query text cannot be empty")
    
    # Load model
    embedding_model = EmbeddingModel()
    model = embedding_model.get_model()
    
    logger.info(f"Generating embedding for query: {query_text[:50]}...")
    
    try:
        # Generate embedding for the query
        query_embedding = model.encode(
            query_text,
            convert_to_numpy=True,
            normalize_embeddings=True
        )
        
        logger.info(f"✓ Query embedding generated: dimension={len(query_embedding)}")
        
        return query_embedding
    
    except Exception as e:
        logger.error(f"Error generating query embedding: {str(e)}")
        raise RuntimeError(f"Failed to generate query embedding: {str(e)}")


def calculate_similarity(embedding1: np.ndarray, embedding2: np.ndarray) -> float:
    """
    Calculates cosine similarity between two embeddings.
    
    Args:
        embedding1: First embedding vector
        embedding2: Second embedding vector
        
    Returns:
        Similarity score between -1 and 1 (higher = more similar)
        
    Academic Note (Cosine Similarity):
    - Measures angle between two vectors
    - Formula: cos(θ) = (A · B) / (||A|| × ||B||)
    - Range: -1 (opposite) to 1 (identical)
    - 0 = orthogonal (unrelated)
    
    Why Cosine (not Euclidean distance)?
    - Direction matters more than magnitude
    - Normalized embeddings → cosine similarity = dot product
    - More robust to vector length variations
    
    Example:
    embedding1 = [1, 0, 0]  (vector pointing right)
    embedding2 = [1, 1, 0]  (vector pointing up-right)
    similarity = cos(45°) ≈ 0.707
    """
    
    # Ensure inputs are numpy arrays
    if not isinstance(embedding1, np.ndarray):
        embedding1 = np.array(embedding1)
    if not isinstance(embedding2, np.ndarray):
        embedding2 = np.array(embedding2)
    
    # Calculate cosine similarity
    # If embeddings are normalized, this is just the dot product
    dot_product = np.dot(embedding1, embedding2)
    norm1 = np.linalg.norm(embedding1)
    norm2 = np.linalg.norm(embedding2)
    
    # Avoid division by zero
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    similarity = dot_product / (norm1 * norm2)
    
    return float(similarity)


# ==============================================================================
# EXAMPLE USAGE (for testing)
# ==============================================================================
if __name__ == "__main__":
    print("=" * 60)
    print("EMBEDDING MODULE TEST")
    print("=" * 60)
    
    # Sample chunks (as would come from chunker.py)
    sample_chunks = [
        {
            "chunk_id": "chunk-001",
            "document_id": "doc-123",
            "chunk_text": "Machine learning is a subset of artificial intelligence.",
            "chunk_index": 0
        },
        {
            "chunk_id": "chunk-002",
            "document_id": "doc-123",
            "chunk_text": "Deep learning uses neural networks with multiple layers.",
            "chunk_index": 1
        },
        {
            "chunk_id": "chunk-003",
            "document_id": "doc-123",
            "chunk_text": "Natural language processing enables computers to understand text.",
            "chunk_index": 2
        }
    ]
    
    # -------------------------------------------------------------------------
    # Test 1: Generate embeddings for chunks
    # -------------------------------------------------------------------------
    print("\n[Test 1] Generating embeddings for chunks...")
    embedded_chunks = generate_embeddings(sample_chunks)
    
    for i, chunk in enumerate(embedded_chunks):
        print(f"\nChunk {i}:")
        print(f"  ID: {chunk['chunk_id']}")
        print(f"  Document: {chunk['document_id']}")
        print(f"  Dimension: {chunk['embedding_dimension']}")
        print(f"  Embedding (first 5 values): {chunk['embedding'][:5]}")
    
    # -------------------------------------------------------------------------
    # Test 2: Generate query embedding
    # -------------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("[Test 2] Generating query embedding...")
    
    query = "What is machine learning?"
    query_embedding = generate_query_embedding(query)
    
    print(f"Query: {query}")
    print(f"Embedding dimension: {len(query_embedding)}")
    print(f"Embedding (first 5 values): {query_embedding[:5]}")
    
    # -------------------------------------------------------------------------
    # Test 3: Calculate similarities
    # -------------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("[Test 3] Calculating similarities with query...")
    
    for i, chunk in enumerate(embedded_chunks):
        chunk_embedding = np.array(chunk['embedding'])
        similarity = calculate_similarity(query_embedding, chunk_embedding)
        
        print(f"\nChunk {i}: {sample_chunks[i]['chunk_text'][:50]}...")
        print(f"  Similarity: {similarity:.4f}")
    
    print("\n" + "=" * 60)
    print("✓ All tests completed successfully!")
    print("=" * 60)