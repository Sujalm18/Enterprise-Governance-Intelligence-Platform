import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np
import faiss

from backend.app.config import settings
from backend.app.services.rag.embedder import EmbeddingService

logger = logging.getLogger("governance_copilot.rag.retrieval")

# Define storage paths using configuration DATA_DIR
DATA_DIR = Path(settings.UPLOAD_DIR).parent
FAISS_STORE_FILE = DATA_DIR / "rag_store.faiss"
METADATA_STORE_FILE = DATA_DIR / "rag_metadata.json"
EMBEDDING_DIM = 384  # Dimension of all-MiniLM-L6-v2 embeddings

class RetrievalService:
    @staticmethod
    def _load_metadata() -> List[Dict[str, Any]]:
        """Loads chunks and their embeddings from the JSON store."""
        if not METADATA_STORE_FILE.exists():
            return []
        try:
            with open(METADATA_STORE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load RAG metadata: {e}")
            return []

    @staticmethod
    def _save_metadata(chunks: List[Dict[str, Any]]) -> None:
        """Saves chunks and their embeddings to the JSON store."""
        try:
            METADATA_STORE_FILE.parent.mkdir(exist_ok=True, parents=True)
            with open(METADATA_STORE_FILE, "w", encoding="utf-8") as f:
                json.dump(chunks, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save RAG metadata: {e}")

    @classmethod
    def _rebuild_faiss_index(cls, all_chunks: List[Dict[str, Any]]) -> None:
        """Rebuilds the FAISS index from the metadata list and saves it to disk."""
        if not all_chunks:
            if FAISS_STORE_FILE.exists():
                try:
                    FAISS_STORE_FILE.unlink()
                except Exception as e:
                    logger.error(f"Failed to delete FAISS store file: {e}")
            return

        try:
            # Gather all embeddings
            embeddings = [c["embedding"] for c in all_chunks]
            embeddings_np = np.array(embeddings, dtype=np.float32)

            # L2 normalize for cosine similarity (Inner Product flat index)
            faiss.normalize_L2(embeddings_np)

            # Create and populate index
            index = faiss.IndexFlatIP(EMBEDDING_DIM)
            index.add(embeddings_np)

            # Save to disk
            faiss.write_index(index, str(FAISS_STORE_FILE))
            logger.info(f"FAISS index successfully rebuilt with {len(all_chunks)} vectors.")
        except Exception as e:
            logger.error(f"Failed to rebuild FAISS index: {e}")

    @classmethod
    def add_chunks(cls, new_chunks: List[Dict[str, Any]]) -> None:
        """
        Generates sentence embeddings for new chunks, updates the metadata store,
        and rebuilds the FAISS index.
        """
        if not new_chunks:
            return

        doc_id = new_chunks[0]["metadata"]["document_id"]
        logger.info(f"Indexing {len(new_chunks)} chunks for document ID: {doc_id}")

        # 1. Generate embeddings for the new chunks
        texts = [c["text"] for c in new_chunks]
        embeddings = EmbeddingService.get_embeddings_batch(texts)

        # 2. Attach embeddings to chunks
        for idx, chunk in enumerate(new_chunks):
            chunk["embedding"] = embeddings[idx]

        # 3. Update metadata store
        all_chunks = cls._load_metadata()
        
        # Remove any existing chunks for this document to avoid duplicates
        all_chunks = [c for c in all_chunks if c["metadata"]["document_id"] != doc_id]
        
        # Append new chunks
        all_chunks.extend(new_chunks)
        cls._save_metadata(all_chunks)

        # 4. Rebuild index
        cls._rebuild_faiss_index(all_chunks)
        logger.info("RAG vector store and index updated successfully.")

    @classmethod
    def delete_chunks(cls, document_id: int) -> None:
        """Removes chunks and embeddings for a specific document and rebuilds index."""
        all_chunks = cls._load_metadata()
        filtered_chunks = [c for c in all_chunks if c["metadata"]["document_id"] != document_id]
        
        if len(filtered_chunks) == len(all_chunks):
            logger.info(f"No chunks found to delete for document ID: {document_id}")
            return
            
        cls._save_metadata(filtered_chunks)
        cls._rebuild_faiss_index(filtered_chunks)
        logger.info(f"Removed chunks and updated index for document ID: {document_id}")

    @classmethod
    def retrieve_relevant_context(
        cls, 
        query: str, 
        document_id: Optional[int] = None, 
        top_k: int = 3,
        score_threshold: float = 0.0
    ) -> str:
        """
        Generates query embedding and runs a similarity search.
        If document_id is specified, constrains the search to that document.
        Returns concatenated text of the top_k matching chunks.
        """
        if not query.strip():
            return ""

        # 1. Load metadata
        all_chunks = cls._load_metadata()
        if not all_chunks:
            logger.warning("RAG metadata store is empty.")
            return ""

        # 2. Filter metadata by document_id if provided
        if document_id is not None:
            filtered_chunks = [c for c in all_chunks if c["metadata"]["document_id"] == document_id]
        else:
            filtered_chunks = all_chunks

        if not filtered_chunks:
            logger.warning(f"No chunks available for search (document_id: {document_id}).")
            return ""

        # If matching chunks are fewer than top_k, return everything
        if len(filtered_chunks) <= top_k:
            return "\n\n".join(c["text"] for c in filtered_chunks)

        # 3. Generate query embedding
        query_embedding = EmbeddingService.get_embedding(query)
        query_np = np.array([query_embedding], dtype=np.float32)
        faiss.normalize_L2(query_np)

        # 4. Build temporary FAISS index for filtered subset (extremely fast and guarantees exact match)
        try:
            subset_embeddings = [c["embedding"] for c in filtered_chunks]
            subset_np = np.array(subset_embeddings, dtype=np.float32)
            faiss.normalize_L2(subset_np)

            temp_index = faiss.IndexFlatIP(EMBEDDING_DIM)
            temp_index.add(subset_np)

            # Search
            D, I = temp_index.search(query_np, top_k)
            scores = D[0]
            indices = I[0]

            retrieved_texts = []
            for rank, idx in enumerate(indices):
                if idx < 0 or idx >= len(filtered_chunks):
                    continue
                score = scores[rank]
                if score >= score_threshold:
                    retrieved_texts.append(filtered_chunks[idx]["text"])
                    
            logger.info(f"Retrieved {len(retrieved_texts)} chunks. Top similarity score: {scores[0]:.4f}")
            return "\n\n".join(retrieved_texts)
        except Exception as e:
            logger.error(f"Error during similarity search: {e}")
            # Fallback to returning first top_k items
            return "\n\n".join(c["text"] for c in filtered_chunks[:top_k])
