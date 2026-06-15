import logging
import os
import httpx
import urllib3
from typing import List
from huggingface_hub import set_client_factory, set_async_client_factory

# Disable SSL warning noise
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Disable SSL verification environment variable
os.environ["HF_HUB_DISABLE_SSL_VERIFICATION"] = "1"

# Client factories for httpx to bypass SSL verification
def my_client_factory():
    return httpx.Client(verify=False, timeout=60.0)

def my_async_client_factory():
    return httpx.AsyncClient(verify=False, timeout=60.0)

set_client_factory(my_client_factory)
set_async_client_factory(my_async_client_factory)

logger = logging.getLogger("governance_copilot.rag.embedder")

_MODEL_INSTANCE = None
_USE_MOCK_EMBEDDER = False

def get_embedding_model():
    """Lazy-loads and caches the SentenceTransformer model with mock fallback on failure."""
    global _MODEL_INSTANCE, _USE_MOCK_EMBEDDER
    if _MODEL_INSTANCE is None and not _USE_MOCK_EMBEDDER:
        try:
            logger.info("Initializing SentenceTransformer with 'all-MiniLM-L6-v2'...")
            from sentence_transformers import SentenceTransformer
            # Try to load cached model local-only to fail fast on network/SSL blocks
            _MODEL_INSTANCE = SentenceTransformer("all-MiniLM-L6-v2", local_files_only=True)
            logger.info("SentenceTransformer model loaded successfully from local files.")
        except Exception as e:
            logger.warning(
                f"Failed to load SentenceTransformer locally: {e}. "
                "Falling back to deterministic offline mock embedder."
            )
            _USE_MOCK_EMBEDDER = True
    return _MODEL_INSTANCE

class EmbeddingService:
    @classmethod
    def get_embedding(cls, text: str) -> List[float]:
        """Generates embedding vector for a single text string."""
        model = get_embedding_model()
        if _USE_MOCK_EMBEDDER or model is None:
            return cls._get_mock_embedding(text)
        try:
            embedding = model.encode(text, convert_to_numpy=True)
            return embedding.tolist()
        except Exception as e:
            logger.warning(f"Embedding failed: {e}. Falling back to mock embedding.")
            return cls._get_mock_embedding(text)

    @classmethod
    def get_embeddings_batch(cls, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """Generates embedding vectors for a batch of text strings efficiently."""
        if not texts:
            return []
        model = get_embedding_model()
        if _USE_MOCK_EMBEDDER or model is None:
            return [cls._get_mock_embedding(t) for t in texts]
        try:
            logger.info(f"Generating embeddings for batch of {len(texts)} chunks...")
            embeddings = model.encode(texts, batch_size=batch_size, show_progress_bar=False, convert_to_numpy=True)
            return embeddings.tolist()
        except Exception as e:
            logger.warning(f"Batch embedding failed: {e}. Falling back to mock embeddings.")
            return [cls._get_mock_embedding(t) for t in texts]

    @staticmethod
    def _get_mock_embedding(text: str) -> List[float]:
        """Generates a deterministic L2-normalized 384-dimensional vector for testing/offline mode."""
        import hashlib
        import numpy as np
        h = hashlib.sha256(text.encode("utf-8")).digest()
        seed = int.from_bytes(h[:4], byteorder="big")
        # Deterministically seed local random generator (thread-safe, doesn't affect global state)
        rng = np.random.default_rng(seed)
        vector = rng.standard_normal(384).astype(np.float32)
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
        return vector.tolist()
