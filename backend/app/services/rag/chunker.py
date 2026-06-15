import logging
import re
from typing import List, Dict, Any

logger = logging.getLogger("governance_copilot.rag.chunker")

def _detect_section(text: str, current_section: str) -> str:
    """Detects if a text block contains a section heading, returning the updated section name."""
    trimmed = text.strip()
    if not trimmed:
        return current_section
    
    # Split into lines; a heading is usually a single short line
    lines = trimmed.splitlines()
    if len(lines) == 1:
        line = lines[0].strip()
        # Keep heading detection constrained to reasonably short lines
        if len(line) < 80 and not line.endswith((".", "?", "!")):
            # Matches "1. Introduction", "1.2.3 Plan", "Section 1: ...", "EXECUTIVE SUMMARY", "I. Summary"
            if (re.match(r"^(\d+(\.\d+)*|[IVXLCDM]+)\.?\s+[A-Za-z]", line) or 
                line.isupper() or 
                re.match(r"^(Section|Chapter|Phase|Part|Appendix|Table|Figure)\s+\d+", line, re.IGNORECASE)):
                return line
    return current_section

def chunk_document_semantically(
    text: str,
    document_id: int,
    filename: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 200
) -> List[Dict[str, Any]]:
    """
    Chunks text by paragraph/semantic boundaries with configurable overlap.
    Preserves document metadata, estimated page number, and detected section heading.
    
    Returns a list of chunk dicts:
    [
        {
            "chunk_index": int,
            "text": str,
            "metadata": {
                "document_id": int,
                "filename": str,
                "chunk_index": int,
                "source_type": str,
                "section": str,
                "page_number": int
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

    logger.info(f"Semantically chunking {filename} (ID: {document_id}) with size {chunk_size}, overlap {chunk_overlap}")
    
    # Track page numbers if form feeds are present (standard in many PDF extractions)
    pages = text.split("\x0c")
    all_chunks = []
    chunk_index = 0
    source_type = filename.split(".")[-1].lower() if "." in filename else "txt"
    
    current_section = "Introduction/Header"
    
    for page_idx, page_content in enumerate(pages, start=1):
        # Split page content into paragraphs/blocks (separated by double or single newlines)
        paragraphs = re.split(r"\n\s*\n", page_content)
        
        current_chunk_paragraphs = []
        current_chunk_len = 0
        
        idx = 0
        while idx < len(paragraphs):
            para = paragraphs[idx].strip()
            if not para:
                idx += 1
                continue
                
            # Keep track of active section heading
            detected_section = _detect_section(para, current_section)
            
            # If a new section is detected, flush the current chunk first to avoid cross-section bleed
            if detected_section != current_section and current_chunk_paragraphs:
                chunk_text = "\n\n".join(current_chunk_paragraphs)
                all_chunks.append({
                    "chunk_index": chunk_index,
                    "text": chunk_text,
                    "metadata": {
                        "document_id": document_id,
                        "filename": filename,
                        "chunk_index": chunk_index,
                        "source_type": source_type,
                        "section": current_section,
                        "page_number": page_idx
                    }
                })
                chunk_index += 1
                current_chunk_paragraphs = []
                current_chunk_len = 0
            
            current_section = detected_section
            para_len = len(para)
            
            # If a single paragraph is larger than chunk_size, we split it by character chunking
            if para_len > chunk_size:
                # Flush the current chunk first
                if current_chunk_paragraphs:
                    chunk_text = "\n\n".join(current_chunk_paragraphs)
                    all_chunks.append({
                        "chunk_index": chunk_index,
                        "text": chunk_text,
                        "metadata": {
                            "document_id": document_id,
                            "filename": filename,
                            "chunk_index": chunk_index,
                            "source_type": source_type,
                            "section": current_section,
                            "page_number": page_idx
                        }
                    })
                    chunk_index += 1
                    current_chunk_paragraphs = []
                    current_chunk_len = 0
                
                # Split this large paragraph into sub-chunks
                start_char = 0
                while start_char < para_len:
                    end_char = min(start_char + chunk_size, para_len)
                    sub_text = para[start_char:end_char]
                    all_chunks.append({
                        "chunk_index": chunk_index,
                        "text": sub_text,
                        "metadata": {
                            "document_id": document_id,
                            "filename": filename,
                            "chunk_index": chunk_index,
                            "source_type": source_type,
                            "section": current_section,
                            "page_number": page_idx
                        }
                    })
                    chunk_index += 1
                    if end_char == para_len:
                        break
                    start_char += (chunk_size - chunk_overlap)
                idx += 1
                continue
                
            # If adding this paragraph would exceed chunk_size
            if current_chunk_len + (2 if current_chunk_paragraphs else 0) + para_len > chunk_size:
                # Flush current chunk
                chunk_text = "\n\n".join(current_chunk_paragraphs)
                all_chunks.append({
                    "chunk_index": chunk_index,
                    "text": chunk_text,
                    "metadata": {
                        "document_id": document_id,
                        "filename": filename,
                        "chunk_index": chunk_index,
                        "source_type": source_type,
                        "section": current_section,
                        "page_number": page_idx
                    }
                })
                chunk_index += 1
                
                # Backtrack to support paragraph-level overlap
                # Find how many previous paragraphs we can fit into the overlap size
                overlap_paras = []
                overlap_len = 0
                for p in reversed(current_chunk_paragraphs):
                    p_len = len(p)
                    if overlap_len + (2 if overlap_paras else 0) + p_len <= chunk_overlap:
                        overlap_paras.insert(0, p)
                        overlap_len += (2 if overlap_paras else 0) + p_len
                    else:
                        break
                
                current_chunk_paragraphs = overlap_paras
                current_chunk_len = overlap_len
            
            # Add paragraph to chunk
            current_chunk_paragraphs.append(para)
            current_chunk_len += (2 if current_chunk_len > 0 else 0) + para_len
            idx += 1
            
        # Flush any remaining paragraphs on the page
        if current_chunk_paragraphs:
            chunk_text = "\n\n".join(current_chunk_paragraphs)
            all_chunks.append({
                "chunk_index": chunk_index,
                "text": chunk_text,
                "metadata": {
                    "document_id": document_id,
                    "filename": filename,
                    "chunk_index": chunk_index,
                    "source_type": source_type,
                    "section": current_section,
                    "page_number": page_idx
                }
            })
            chunk_index += 1

    logger.info(f"Semantically split text into {len(all_chunks)} chunks.")
    return all_chunks
