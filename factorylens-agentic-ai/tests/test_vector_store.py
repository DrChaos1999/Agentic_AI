import numpy as np

from app.retrieval.faiss_store import FaissVectorStore


def test_vector_store_returns_nearest_item(tmp_path):
    vectors = np.eye(3, dtype="float32")
    metadata = [{"label": "a"}, {"label": "b"}, {"label": "c"}]
    store = FaissVectorStore("flat")
    store.build(vectors, metadata)
    result = store.search(np.array([0.0, 1.0, 0.0], dtype="float32"), top_k=1)
    assert result[0]["label"] == "b"
    assert result[0]["score"] > 0.99


def test_vector_store_round_trip(tmp_path):
    store = FaissVectorStore("flat")
    store.build(np.eye(2, dtype="float32"), [{"id": 1}, {"id": 2}])
    index = tmp_path / "index.bin"
    metadata = tmp_path / "metadata.json"
    vectors = tmp_path / "vectors.npy"
    store.save(index, metadata, vectors)
    loaded = FaissVectorStore.load(index, metadata, vectors)
    assert loaded.size == 2
    assert loaded.search(np.array([1.0, 0.0], dtype="float32"), 1)[0]["id"] == 1
