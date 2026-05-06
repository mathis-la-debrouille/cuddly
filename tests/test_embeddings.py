from __future__ import annotations

import pytest


@pytest.mark.slow
def test_embed_shape() -> None:
    from cuddly.embeddings.embedder import Embedder
    embedder = Embedder()
    vecs = embedder.embed(["hello world", "test code"])
    assert vecs.shape == (2, 384)


@pytest.mark.slow
def test_embed_one_shape() -> None:
    from cuddly.embeddings.embedder import Embedder
    embedder = Embedder()
    vec = embedder.embed_one("hello")
    assert vec.shape == (384,)


@pytest.mark.slow
def test_embed_normalized() -> None:
    import numpy as np
    from cuddly.embeddings.embedder import Embedder
    embedder = Embedder()
    vec = embedder.embed_one("test")
    norm = float(np.linalg.norm(vec))
    assert abs(norm - 1.0) < 1e-4  # normalize_embeddings=True
