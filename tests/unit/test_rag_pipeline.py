import os
import pytest
from pathlib import Path
import shutil

from backend.app.services.rag.chunker import chunk_document_semantically
from backend.app.services.rag.embedder import EmbeddingService
from backend.app.services.rag.retrieval import RetrievalService, METADATA_STORE_FILE, FAISS_STORE_FILE

def test_semantic_chunker():
    text = "Section 1: Executive Briefing\n\nThis is paragraph one of the first section. It has some important details.\n\nThis is paragraph two. It continues the discussion.\n\nSection 2: Risk Assessment\n\nThis is a risk assessment paragraph. High risk of failure detected."
    
    chunks = chunk_document_semantically(
        text=text,
        document_id=42,
        filename="project_charter.pdf",
        chunk_size=300,
        chunk_overlap=50
    )
    
    assert len(chunks) > 0
    # Check structure
    for idx, c in enumerate(chunks):
        assert c["chunk_index"] == idx
        assert c["metadata"]["document_id"] == 42
        assert c["metadata"]["filename"] == "project_charter.pdf"
        assert c["metadata"]["source_type"] == "pdf"
        assert "section" in c["metadata"]
        assert c["metadata"]["page_number"] == 1
        
    # Verify section headings are tracked
    first_chunk = chunks[0]
    assert "Section 1" in first_chunk["metadata"]["section"]
    
    # Check section change detection
    last_chunk = chunks[-1]
    assert "Section 2" in last_chunk["metadata"]["section"]

def test_embedding_service():
    text = "Enterprise AI Governance Copilot"
    vector = EmbeddingService.get_embedding(text)
    
    assert isinstance(vector, list)
    assert len(vector) == 384
    assert all(isinstance(x, float) for x in vector)
    
    texts = ["Project Alpha", "Project Beta", "Risk Mitigation"]
    vectors = EmbeddingService.get_embeddings_batch(texts)
    
    assert isinstance(vectors, list)
    assert len(vectors) == 3
    assert len(vectors[0]) == 384

def test_retrieval_service():
    # Setup temporary RAG files for testing (preserving existing ones if any)
    backup_meta = None
    backup_faiss = None
    
    if METADATA_STORE_FILE.exists():
        backup_meta = METADATA_STORE_FILE.with_suffix(".json.bak")
        shutil.copy2(METADATA_STORE_FILE, backup_meta)
        METADATA_STORE_FILE.unlink()
        
    if FAISS_STORE_FILE.exists():
        backup_faiss = FAISS_STORE_FILE.with_suffix(".faiss.bak")
        shutil.copy2(FAISS_STORE_FILE, backup_faiss)
        FAISS_STORE_FILE.unlink()
        
    try:
        # 1. Add chunks for Doc 1
        chunks_doc1 = [
            {
                "chunk_index": 0,
                "text": "The primary risk for Project Apollo is budget overrun. We estimate a 20% budget gap.",
                "metadata": {"document_id": 1, "filename": "apollo.txt", "chunk_index": 0, "source_type": "txt", "section": "Summary", "page_number": 1}
            },
            {
                "chunk_index": 1,
                "text": "Mitigation: Project Apollo will trim scope by deferring feature set X.",
                "metadata": {"document_id": 1, "filename": "apollo.txt", "chunk_index": 1, "source_type": "txt", "section": "Mitigation", "page_number": 1}
            }
        ]
        
        # 2. Add chunks for Doc 2
        chunks_doc2 = [
            {
                "chunk_index": 0,
                "text": "Project Artemis is on schedule. Main challenge is resource constraints in the design team.",
                "metadata": {"document_id": 2, "filename": "artemis.txt", "chunk_index": 0, "source_type": "txt", "section": "Summary", "page_number": 1}
            }
        ]
        
        RetrievalService.add_chunks(chunks_doc1)
        assert METADATA_STORE_FILE.exists()
        assert FAISS_STORE_FILE.exists()
        
        RetrievalService.add_chunks(chunks_doc2)
        
        # Verify metadata store contains both documents
        all_metadata = RetrievalService._load_metadata()
        doc_ids = {c["metadata"]["document_id"] for c in all_metadata}
        assert doc_ids == {1, 2}
        assert len(all_metadata) == 3
        
        # 3. Test Retrieval
        # Test Doc 1 scope
        context_doc1 = RetrievalService.retrieve_relevant_context(
            query="What are the risks of budget overruns?",
            document_id=1,
            top_k=1
        )
        assert "Project Apollo" in context_doc1
        assert "Artemis" not in context_doc1
        
        # Test Doc 2 scope
        context_doc2 = RetrievalService.retrieve_relevant_context(
            query="Is Project Artemis on schedule?",
            document_id=2,
            top_k=1
        )
        assert "Artemis" in context_doc2
        assert "Apollo" not in context_doc2
        
        # Test overall search (cross-document)
        context_all = RetrievalService.retrieve_relevant_context(
            query="Project Artemis is on schedule. Main challenge is resource constraints in the design team.",
            document_id=None,
            top_k=1
        )
        assert "Artemis" in context_all
        
        # 4. Test deletion
        RetrievalService.delete_chunks(1)
        all_metadata_post_delete = RetrievalService._load_metadata()
        doc_ids_post_delete = {c["metadata"]["document_id"] for c in all_metadata_post_delete}
        assert doc_ids_post_delete == {2}
        assert len(all_metadata_post_delete) == 1
        
        # Verify FAISS search only hits remaining doc
        context_final = RetrievalService.retrieve_relevant_context(
            query="budget overrun",
            document_id=None,
            top_k=1
        )
        assert "Apollo" not in context_final
        
    finally:
        # Cleanup test files and restore backups if they existed
        if METADATA_STORE_FILE.exists():
            METADATA_STORE_FILE.unlink()
        if FAISS_STORE_FILE.exists():
            FAISS_STORE_FILE.unlink()
            
        if backup_meta is not None:
            shutil.copy2(backup_meta, METADATA_STORE_FILE)
            backup_meta.unlink()
        if backup_faiss is not None:
            shutil.copy2(backup_faiss, FAISS_STORE_FILE)
            backup_faiss.unlink()
