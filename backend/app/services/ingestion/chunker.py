import logging
from typing import List, Dict, Any

logger = logging.getLogger("governance_copilot.ingestion.chunker")

def chunk_text(
    text: str,
    document_id: int,
    filename: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 200
) -> List[Dict[str, Any]]:
    """
    Chunks a text string into overlapping chunks.
    Deterministic behavior based on character indices.
    
    Returns a list of dicts:
    [
        {
            "chunk_index": int,
            "text": str,
            "metadata": {
                "document_id": int,
                "filename": str,
                "chunk_index": int,
                "source_type": str
            }
        },
        ...
    ]
    """
    if not text:
        return []
        
    if chunk_size <= 0:
        raise ValueError("chunk_size must be a positive integer")
    if chunk_overlap < 0 or chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be non-negative and strictly less than chunk_size")
        
    logger.info(f"Chunking document ID {document_id} with size {chunk_size} and overlap {chunk_overlap}")
    
    chunks = []
    text_length = len(text)
    start = 0
    chunk_index = 0
    
    # Retrieve file extension as source type
    source_type = filename.split(".")[-1].lower() if "." in filename else "txt"
    
    while start < text_length:
        end = min(start + chunk_size, text_length)
        chunk_text_data = text[start:end]
        
        chunks.append({
            "chunk_index": chunk_index,
            "text": chunk_text_data,
            "metadata": {
                "document_id": document_id,
                "filename": filename,
                "chunk_index": chunk_index,
                "source_type": source_type
            }
        })
        
        # Advance the pointer
        if end == text_length:
            break
        start += (chunk_size - chunk_overlap)
        chunk_index += 1
        
    logger.info(f"Split text into {len(chunks)} chunks.")
    return chunks
