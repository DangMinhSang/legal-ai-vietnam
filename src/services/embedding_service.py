"""Text embedding service using fastembed with in-memory caching and singleton pattern.

Provides:
- EmbeddingService: Singleton service for generating dense vector embeddings
  via fastembed (ONNX runtime) with LRU caching, text truncation, and graceful
  fallback to zero vectors when fastembed or weights are unavailable.
"""

from __future__ import annotations

import time
from collections import OrderedDict
from typing import Any, Optional

from loguru import logger

try:
    from fastembed import TextEmbedding
    FASTEMBED_AVAILABLE = True
except ImportError:
    FASTEMBED_AVAILABLE = False


class EmbeddingService:
    """Singleton service for generating text embeddings using fastembed.

    Features:
    - Singleton pattern with class-level `_instance`.
    - Lazy model loading: loads fastembed weights on first use, not in `__init__`.
    - In-memory LRU cache (up to 1000 entries) using hash of text string as key.
    - Automatic text truncation to max 2048 characters.
    - Model load time and batch processing time logged via loguru.
    - Graceful fallback: returns 768-dimensional zero vectors if fastembed is unavailable.
    """

    _instance: Optional["EmbeddingService"] = None

    def __new__(cls, *args: Any, **kwargs: Any) -> "EmbeddingService":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(
        self,
        model_name: str = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
        cache_dir: Optional[str] = None,
        batch_size: int = 32,
    ) -> None:
        """Initialize EmbeddingService parameters without loading the model.

        Args:
            model_name: HuggingFace model identifier for fastembed.
            cache_dir: Optional directory for caching model weights.
            batch_size: Batch size for embedding generation.
        """
        if getattr(self, "_initialized", False):
            return

        self.model_name = model_name
        self.cache_dir = cache_dir
        self.batch_size = batch_size
        self._model: Optional[Any] = None
        self._embedding_dim = 768
        self._max_chars = 2048
        self._cache_max_entries = 1000
        # In-memory LRU cache: hash(text) -> list[float]
        self._cache: OrderedDict[int, list[float]] = OrderedDict()
        self._load_attempted = False
        self._initialized = True

    @classmethod
    def get_instance(
        cls,
        model_name: str = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
        cache_dir: Optional[str] = None,
        batch_size: int = 32,
    ) -> "EmbeddingService":
        """Retrieve or create the singleton instance."""
        if cls._instance is None:
            cls._instance = cls(
                model_name=model_name,
                cache_dir=cache_dir,
                batch_size=batch_size,
            )
        return cls._instance

    @classmethod
    def _reset_instance(cls) -> None:
        """Reset the singleton instance (useful in unit testing)."""
        cls._instance = None

    def _deterministic_vector(self, text: str) -> list[float]:
        """Tạo vector 768-dim chuẩn hoá từ hash chuỗi khi model chưa tải hoặc offline."""
        seed = sum(ord(c) for c in text[:128]) + len(text)
        vec = [float((seed * (i + 1)) % 100) / 100.0 for i in range(self._embedding_dim)]
        norm = sum(x * x for x in vec) ** 0.5 or 1.0
        return [x / norm for x in vec]

    def _get_model(self) -> Optional[Any]:
        """Lazy load the fastembed TextEmbedding model on first usage."""
        import os
        if os.environ.get("FAST_MOCK_EMBEDDING") == "1" or os.environ.get("OFFLINE_MODE") == "1":
            return None

        if not FASTEMBED_AVAILABLE:
            logger.warning(
                "fastembed is not installed; EmbeddingService running in graceful fallback mode."
            )
            return None

        if self._model is None and not self._load_attempted:
            self._load_attempted = True
            start_time = time.perf_counter()
            logger.info(f"Loading fastembed TextEmbedding model: '{self.model_name}'...")
            try:
                # Cho phép tự động tải từ HuggingFace Hub hoặc đọc từ local cache
                allow_download = os.environ.get("ALLOW_MODEL_DOWNLOAD", "1") == "1"
                self._model = TextEmbedding(
                    model_name=self.model_name,
                    cache_dir=self.cache_dir,
                    local_files_only=not allow_download,
                )
                duration = time.perf_counter() - start_time
                logger.info(f"Embedding model '{self.model_name}' loaded in {duration:.2f}s.")
            except Exception as e:
                logger.warning(
                    f"Model fastembed '{self.model_name}' chưa có sẵn ở local cache hoặc lỗi load ({e}). "
                    "Chuyển sang deterministic vector fallback mode."
                )
                self._model = None

        return self._model

    def _truncate(self, text: str) -> str:
        """Truncate text if too long (max 2048 characters)."""
        if len(text) > self._max_chars:
            return text[: self._max_chars]
        return text

    def _get_cache_key(self, text: str) -> int:
        """Generate hash key for text string (since list is not hashable)."""
        return hash(text)

    def _get_cached(self, text: str) -> Optional[list[float]]:
        """Retrieve embedding from in-memory LRU cache if present."""
        key = self._get_cache_key(text)
        if key in self._cache:
            self._cache.move_to_end(key)
            return self._cache[key]
        return None

    def _put_cached(self, text: str, embedding: list[float]) -> None:
        """Store embedding in LRU cache with eviction of oldest entry when full."""
        key = self._get_cache_key(text)
        if key in self._cache:
            self._cache.move_to_end(key)
        self._cache[key] = embedding
        if len(self._cache) > self._cache_max_entries:
            self._cache.popitem(last=False)

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a list of texts in batches.

        Args:
            texts: List of text strings to embed.

        Returns:
            List of 768-dimensional float embedding vectors.
        """
        if not texts:
            return []

        clean_texts = [self._truncate(t.strip()) for t in texts]
        results: list[Optional[list[float]]] = [None] * len(clean_texts)
        missing_indices: list[int] = []
        missing_texts: list[str] = []

        # Check in-memory LRU cache first
        for idx, text in enumerate(clean_texts):
            cached = self._get_cached(text)
            if cached is not None:
                results[idx] = cached
            else:
                missing_indices.append(idx)
                missing_texts.append(text)

        # Compute embeddings for cache misses
        if missing_texts:
            model = self._get_model()
            start_time = time.perf_counter()

            if model is not None:
                try:
                    embeddings_gen = model.embed(missing_texts, batch_size=self.batch_size)
                    embeddings_list: list[list[float]] = [
                        emb.tolist() if hasattr(emb, "tolist") else list(map(float, emb))
                        for emb in embeddings_gen
                    ]
                    duration = time.perf_counter() - start_time
                    speed = len(missing_texts) / max(duration, 0.0001)
                    logger.info(
                        f"Embedded {len(missing_texts)} texts in {duration:.3f}s ({speed:.1f} texts/s)."
                    )

                    for idx, emb, raw_text in zip(missing_indices, embeddings_list, missing_texts):
                        results[idx] = emb
                        self._put_cached(raw_text, emb)
                except Exception as e:
                    logger.error(f"Error during batch embedding generation: {e}")
                    for i, idx in enumerate(missing_indices):
                        emb = self._deterministic_vector(missing_texts[i])
                        results[idx] = emb
                        self._put_cached(missing_texts[i], emb)
            else:
                # Graceful deterministic fallback
                duration = time.perf_counter() - start_time
                logger.warning(
                    f"Using deterministic fallback vectors for {len(missing_texts)} texts (fastembed unavailable)."
                )
                for i, idx in enumerate(missing_indices):
                    emb = self._deterministic_vector(missing_texts[i])
                    results[idx] = emb
                    self._put_cached(missing_texts[i], emb)

        return [r if r is not None else [0.0] * self._embedding_dim for r in results]

    def embed_single(self, text: str) -> list[float]:
        """Generate embedding vector for a single text string.

        Args:
            text: Text to embed.

        Returns:
            768-dimensional float embedding vector.
        """
        result = self.embed_texts([text])
        return result[0] if result else [0.0] * self._embedding_dim

    def embed_query(self, query: str) -> list[float]:
        """Generate embedding for a search query.

        Semantically distinct from embed_single, allowing for asymmetric
        search models or query prefixing.

        Args:
            query: Query text.

        Returns:
            768-dimensional float embedding vector.
        """
        return self.embed_single(query)

    def embed_text(self, text: str) -> list[float]:
        """Convenience alias for embed_single."""
        return self.embed_single(text)

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Convenience alias for embed_texts."""
        return self.embed_texts(texts)
