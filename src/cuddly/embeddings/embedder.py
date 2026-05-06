from __future__ import annotations

import numpy as np
from sentence_transformers import SentenceTransformer


class Embedder:
    """Wraps sentence-transformers with lazy model loading."""

    _model: SentenceTransformer | None = None

    def __init__(self) -> None:
        from cuddly.config import get_config
        self._config = get_config()

    def _load(self) -> SentenceTransformer:
        if self._model is None:
            self._model = SentenceTransformer(
                self._config.embed_model,
                device=self._config.embed_device,
            )
        return self._model

    def embed(self, texts: list[str]) -> np.ndarray:
        model = self._load()
        return model.encode(
            texts,
            batch_size=32,
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )

    def embed_one(self, text: str) -> np.ndarray:
        return self.embed([text])[0]
