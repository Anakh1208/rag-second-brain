"""
app/rag/chunker.py
------------------
Text Chunking Module for RAG Pipeline

Academic Note (for SEPM viva):
- Implements sliding window chunking with configurable overlap
- Overlap preserves context across chunk boundaries (important for RAG)
- Deterministic chunking ensures reproducibility
- Simple character-based splitting (suitable for academic prototype)
- In production, might use semantic chunking or sentence-aware splitting

Why Chunking is Necessary:
1. LLMs have token limits (e.g., 4096 tokens for many models)
2. Smaller chunks = more precise retrieval
3. Overlapping chunks = better context preservation
4. Enables efficient vector similarity search
"""

import uuid
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

# ==============================================================================
# CONFIGURATION
# ==============================================================================
# Default chunking parameters
DEFAULT_CHUNK_SIZE = 500  # Characters per chunk
DEFAULT_OVERLAP = 100     # Overlapping characters between consecutive chunks

# ==============================================================================
# CHUNKING FUNCTIONS
# ==============================================================================

def create_chunks(
    text: str,
    document_id: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_OVERLAP
) -> List[Dict]:
    """
    Splits text into overlapping chunks for RAG processing.
    
    Args:
        text: Full document text to be chunked
        document_id: UUID of the source document
        chunk_size: Maximum characters per chunk (default: 500)
        overlap: Overlapping characters between chunks (default: 100)
        
    Returns:
        List of chunk dictionaries, each containing:
            - chunk_id: Unique identifier for the chunk
            - document_id: ID of source document
            - chunk_text: Text content of the chunk
            - chunk_index: Sequential position in document (0-indexed)
            - start_char: Starting character position in original text
            - end_char: Ending character position in original text
            
    Academic Note (Chunking Algorithm):
    1. Use sliding window approach with overlap
    2. Overlap ensures context continuity between chunks
    3. Example with chunk_size=10, overlap=3:
       Text: "Hello world from AI"
       Chunk 0: "Hello worl" (chars 0-10)
       Chunk 1: "rld from A" (chars 7-17) ← overlaps 3 chars
       Chunk 2: "m AI"       (chars 14-18) ← overlaps 3 chars
       
    Why This Approach:
    - Simple and deterministic (easy to explain in viva)
    - Overlap prevents information loss at boundaries
    - Character-based (language-agnostic)
    - No external dependencies required
    """
    
    # -------------------------------------------------------------------------
    # STEP 1: Input validation
    # -------------------------------------------------------------------------
    if not text or not text.strip():
        logger.warning(f"Empty text provided for document {document_id}")
        return []
    
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    
    if overlap < 0:
        raise ValueError("overlap cannot be negative")
    
    if overlap >= chunk_size:
        raise ValueError("overlap must be less than chunk_size")
    
    # -------------------------------------------------------------------------
    # STEP 2: Clean text (remove excessive whitespace)
    # -------------------------------------------------------------------------
    # Normalize whitespace while preserving paragraph structure
    cleaned_text = " ".join(text.split())
    
    if len(cleaned_text) == 0:
        logger.warning(f"Text becomes empty after cleaning for document {document_id}")
        return []
    
    # -------------------------------------------------------------------------
    # STEP 3: Calculate chunking parameters
    # -------------------------------------------------------------------------
    text_length = len(cleaned_text)
    step_size = chunk_size - overlap  # How far to move forward each iteration
    
    logger.info(f"Chunking document {document_id}: "
                f"length={text_length}, chunk_size={chunk_size}, "
                f"overlap={overlap}, step_size={step_size}")
    
    # -------------------------------------------------------------------------
    # STEP 4: Create chunks using sliding window
    # -------------------------------------------------------------------------
    chunks = []
    chunk_index = 0
    start_pos = 0
    
    while start_pos < text_length:
        # Calculate end position for current chunk
        end_pos = min(start_pos + chunk_size, text_length)
        
        # Extract chunk text
        chunk_text = cleaned_text[start_pos:end_pos]
        
        # Skip empty chunks (shouldn't happen, but safety check)
        if not chunk_text.strip():
            start_pos += step_size
            continue
        
        # Create chunk metadata
        chunk = {
            "chunk_id": str(uuid.uuid4()),
            "document_id": document_id,
            "chunk_text": chunk_text,
            "chunk_index": chunk_index,
            "start_char": start_pos,
            "end_char": end_pos,
            "chunk_length": len(chunk_text)
        }
        
        chunks.append(chunk)
        
        # Move to next chunk position
        start_pos += step_size
        chunk_index += 1
        
        # Stop if we've reached the end
        if end_pos >= text_length:
            break
    
    logger.info(f"Created {len(chunks)} chunks for document {document_id}")
    
    return chunks


def create_chunks_sentence_aware(
    text: str,
    document_id: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_OVERLAP
) -> List[Dict]:
    """
    Creates chunks with sentence boundary awareness.
    
    Args:
        text: Full document text
        document_id: UUID of source document
        chunk_size: Target characters per chunk
        overlap: Overlapping characters between chunks
        
    Returns:
        List of chunk dictionaries
        
    Academic Note (Advanced Chunking):
    - Attempts to break chunks at sentence boundaries
    - Improves semantic coherence of chunks
    - More complex than basic chunking but produces better results
    - Useful for research paper discussion (show understanding of trade-offs)
    
    Algorithm:
    1. Split text into sentences (using simple punctuation rules)
    2. Group sentences until chunk_size is reached
    3. Apply overlap by including last N characters from previous chunk
    
    Trade-offs vs. Basic Chunking:
    + Better semantic coherence
    + More natural chunk boundaries
    - Slightly more complex
    - Variable chunk sizes (not perfectly uniform)
    """
    
    # -------------------------------------------------------------------------
    # STEP 1: Simple sentence splitting
    # -------------------------------------------------------------------------
    # Split on common sentence endings (., !, ?)
    # This is a simplified approach; production systems might use NLP libraries
    import re
    
    # Regex pattern for sentence boundaries
    # Matches: period, exclamation, question mark followed by space or end
    sentence_pattern = r'(?<=[.!?])\s+'
    sentences = re.split(sentence_pattern, text.strip())
    
    if not sentences:
        logger.warning(f"No sentences found in document {document_id}")
        return []
    
    # -------------------------------------------------------------------------
    # STEP 2: Group sentences into chunks
    # -------------------------------------------------------------------------
    chunks = []
    chunk_index = 0
    current_chunk_sentences = []
    current_chunk_length = 0
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        
        sentence_length = len(sentence)
        
        # Check if adding this sentence would exceed chunk_size
        if current_chunk_length + sentence_length > chunk_size and current_chunk_sentences:
            # Create chunk from accumulated sentences
            chunk_text = " ".join(current_chunk_sentences)
            
            chunk = {
                "chunk_id": str(uuid.uuid4()),
                "document_id": document_id,
                "chunk_text": chunk_text,
                "chunk_index": chunk_index,
                "chunk_length": len(chunk_text),
                "sentence_count": len(current_chunk_sentences)
            }
            
            chunks.append(chunk)
            chunk_index += 1
            
            # Apply overlap: keep last N characters
            if overlap > 0 and chunk_text:
                overlap_text = chunk_text[-overlap:] if len(chunk_text) > overlap else chunk_text
                current_chunk_sentences = [overlap_text]
                current_chunk_length = len(overlap_text)
            else:
                current_chunk_sentences = []
                current_chunk_length = 0
        
        # Add current sentence to chunk
        current_chunk_sentences.append(sentence)
        current_chunk_length += sentence_length + 1  # +1 for space
    
    # Add final chunk if any sentences remain
    if current_chunk_sentences:
        chunk_text = " ".join(current_chunk_sentences)
        chunk = {
            "chunk_id": str(uuid.uuid4()),
            "document_id": document_id,
            "chunk_text": chunk_text,
            "chunk_index": chunk_index,
            "chunk_length": len(chunk_text),
            "sentence_count": len(current_chunk_sentences)
        }
        chunks.append(chunk)
    
    logger.info(f"Created {len(chunks)} sentence-aware chunks for document {document_id}")
    
    return chunks


def get_chunk_statistics(chunks: List[Dict]) -> Dict:
    """
    Calculates statistics about a list of chunks.
    
    Args:
        chunks: List of chunk dictionaries
        
    Returns:
        Dictionary with chunking statistics
        
    Academic Note:
    - Useful for analyzing chunking effectiveness
    - Can be used in research paper to show chunking quality
    - Helps tune chunk_size and overlap parameters
    """
    
    if not chunks:
        return {
            "total_chunks": 0,
            "avg_chunk_length": 0,
            "min_chunk_length": 0,
            "max_chunk_length": 0,
            "total_characters": 0
        }
    
    chunk_lengths = [chunk["chunk_length"] for chunk in chunks]
    
    return {
        "total_chunks": len(chunks),
        "avg_chunk_length": sum(chunk_lengths) / len(chunk_lengths),
        "min_chunk_length": min(chunk_lengths),
        "max_chunk_length": max(chunk_lengths),
        "total_characters": sum(chunk_lengths),
        "unique_documents": len(set(chunk["document_id"] for chunk in chunks))
    }


# ==============================================================================
# EXAMPLE USAGE (for testing)
# ==============================================================================
if __name__ == "__main__":
    # Example text for demonstration
    sample_text = """
    Artificial intelligence is transforming the world. Machine learning models
    can now process vast amounts of data. Natural language processing enables
    computers to understand human language. Retrieval-Augmented Generation combines
    retrieval with language models. This approach improves accuracy and reduces
    hallucinations. RAG systems are particularly useful for knowledge management.
    They enable efficient information retrieval from large document collections.
    """
    
    # Test basic chunking
    print("=" * 60)
    print("BASIC CHUNKING TEST")
    print("=" * 60)
    
    basic_chunks = create_chunks(
        text=sample_text,
        document_id="test-doc-123",
        chunk_size=100,
        overlap=20
    )
    
    for i, chunk in enumerate(basic_chunks):
        print(f"\nChunk {i}:")
        print(f"  ID: {chunk['chunk_id']}")
        print(f"  Text: {chunk['chunk_text'][:50]}...")
        print(f"  Length: {chunk['chunk_length']}")
        print(f"  Position: {chunk['start_char']}-{chunk['end_char']}")
    
    # Test sentence-aware chunking
    print("\n" + "=" * 60)
    print("SENTENCE-AWARE CHUNKING TEST")
    print("=" * 60)
    
    sentence_chunks = create_chunks_sentence_aware(
        text=sample_text,
        document_id="test-doc-123",
        chunk_size=150,
        overlap=30
    )
    
    for i, chunk in enumerate(sentence_chunks):
        print(f"\nChunk {i}:")
        print(f"  ID: {chunk['chunk_id']}")
        print(f"  Text: {chunk['chunk_text'][:50]}...")
        print(f"  Length: {chunk['chunk_length']}")
        print(f"  Sentences: {chunk.get('sentence_count', 'N/A')}")
    
    # Statistics
    print("\n" + "=" * 60)
    print("CHUNKING STATISTICS")
    print("=" * 60)
    
    stats = get_chunk_statistics(basic_chunks)
    print(f"\nBasic Chunking Stats:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    stats_sentence = get_chunk_statistics(sentence_chunks)
    print(f"\nSentence-Aware Chunking Stats:")
    for key, value in stats_sentence.items():
        print(f"  {key}: {value}")
