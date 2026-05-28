import json
import logging
import math
import re
from pathlib import Path
from typing import List, Dict, Any, Set
from backend.app.config import settings

logger = logging.getLogger("governance_copilot.rag.retrieval")
STORE_FILE = Path(settings.DATABASE_URL.replace("sqlite:///", "")).parent / "rag_store.json"

class RetrievalService:
    @staticmethod
    def _load_store() -> List[Dict[str, Any]]:
        """Loads chunks from persistent JSON store."""
        if not STORE_FILE.exists():
            return []
        try:
            with open(STORE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load RAG store: {e}")
            return []

    @staticmethod
    def _save_store(chunks: List[Dict[str, Any]]) -> None:
        """Saves chunks to persistent JSON store."""
        try:
            STORE_FILE.parent.mkdir(exist_ok=True, parents=True)
            with open(STORE_FILE, "w", encoding="utf-8") as f:
                json.dump(chunks, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save RAG store: {e}")

    @classmethod
    def add_chunks(cls, new_chunks: List[Dict[str, Any]]) -> None:
        """Adds new chunks to the TF-IDF search database, replacing older ones for same document."""
        if not new_chunks:
            return
            
        doc_id = new_chunks[0]["metadata"]["document_id"]
        logger.info(f"Indexing {len(new_chunks)} chunks for document ID: {doc_id}")
        
        all_chunks = cls._load_store()
        # Remove any existing chunks for this document
        all_chunks = [c for c in all_chunks if c["metadata"]["document_id"] != doc_id]
        # Append new chunks
        all_chunks.extend(new_chunks)
        cls._save_store(all_chunks)
        logger.info("RAG store updated successfully.")

    @classmethod
    def delete_chunks(cls, document_id: int) -> None:
        """Removes chunks for a specific document."""
        all_chunks = cls._load_store()
        all_chunks = [c for c in all_chunks if c["metadata"]["document_id"] != document_id]
        cls._save_store(all_chunks)
        logger.info(f"Removed chunks for document ID: {document_id}")

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        """Simple regex tokenization, lowercased, filtering out short words."""
        text = text.lower()
        words = re.findall(r"\b[a-z]{3,}\b", text)
        return words

    @classmethod
    def retrieve_relevant_context(cls, query: str, document_id: int, top_k: int = 3) -> str:
        """
        Runs TF-IDF and Cosine Similarity search over the document's chunks.
        Returns a single concatenated text string.
        """
        logger.info(f"Retrieving top {top_k} chunks for query: '{query}' in document ID: {document_id}")
        
        all_chunks = cls._load_store()
        # Filter chunks belonging to requested document
        doc_chunks = [c for c in all_chunks if c["metadata"]["document_id"] == document_id]
        
        if not doc_chunks:
            logger.warning(f"No chunks indexed for document ID: {document_id}")
            return ""
            
        # If there are fewer chunks than top_k, return everything
        if len(doc_chunks) <= top_k:
            return "\n\n".join(c["text"] for c in doc_chunks)
            
        # Term Frequency (TF) for each chunk
        chunk_tfs: List[Dict[str, float]] = []
        chunk_tokens_list: List[List[str]] = []
        
        all_terms: Set[str] = set()
        
        for c in doc_chunks:
            tokens = cls._tokenize(c["text"])
            chunk_tokens_list.append(tokens)
            
            tf: Dict[str, float] = {}
            for t in tokens:
                tf[t] = tf.get(t, 0.0) + 1.0
                all_terms.add(t)
                
            # Normalize TF
            total_tokens = len(tokens)
            if total_tokens > 0:
                for t in tf:
                    tf[t] = tf[t] / total_tokens
            chunk_tfs.append(tf)
            
        # Inverse Document Frequency (IDF)
        num_docs = len(doc_chunks)
        idf: Dict[str, float] = {}
        for term in all_terms:
            docs_with_term = sum(1 for tokens in chunk_tokens_list if term in tokens)
            # Standard smooth IDF formula
            idf[term] = math.log((1.0 + num_docs) / (1.0 + docs_with_term)) + 1.0
            
        # Query TF-IDF vector
        query_tokens = cls._tokenize(query)
        if not query_tokens:
            # Query is empty or too short, return first chunks
            return "\n\n".join(c["text"] for c in doc_chunks[:top_k])
            
        query_tf: Dict[str, float] = {}
        for t in query_tokens:
            query_tf[t] = query_tf.get(t, 0.0) + 1.0
            
        query_total = len(query_tokens)
        for t in query_tf:
            query_tf[t] = query_tf[t] / query_total
            
        query_tfidf: Dict[str, float] = {}
        for t, tf_val in query_tf.items():
            if t in idf:
                query_tfidf[t] = tf_val * idf[t]
                
        # Normalize Query Vector length
        query_norm = math.sqrt(sum(v * v for v in query_tfidf.values()))
        if query_norm == 0:
            return "\n\n".join(c["text"] for c in doc_chunks[:top_k])
            
        # Calculate Cosine Similarity for each chunk
        scored_chunks = []
        for idx, tf_dict in enumerate(chunk_tfs):
            chunk_tfidf: Dict[str, float] = {}
            for term, tf_val in tf_dict.items():
                if term in idf:
                    chunk_tfidf[term] = tf_val * idf[term]
                    
            chunk_norm = math.sqrt(sum(v * v for v in chunk_tfidf.values()))
            if chunk_norm == 0:
                similarity = 0.0
            else:
                # Dot Product
                dot_product = sum(query_tfidf[t] * chunk_tfidf[t] for t in query_tfidf if t in chunk_tfidf)
                similarity = dot_product / (query_norm * chunk_norm)
                
            scored_chunks.append((similarity, doc_chunks[idx]))
            
        # Sort by similarity descending
        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        top_chunks = scored_chunks[:top_k]
        
        logger.info(f"Retrieved {len(top_chunks)} chunks. Best similarity score: {top_chunks[0][0]:.4f}")
        
        # Concat retrieved chunks
        return "\n\n".join(chunk_data["text"] for _, chunk_data in top_chunks)
