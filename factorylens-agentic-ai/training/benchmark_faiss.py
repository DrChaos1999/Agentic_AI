from __future__ import annotations

import argparse
import time
from pathlib import Path

import mlflow
import numpy as np

from app.retrieval.faiss_store import FaissVectorStore


def recall_at_k(reference: list[list[int]], candidate: list[list[int]], k: int) -> float:
    values = []
    for expected, actual in zip(reference, candidate, strict=False):
        values.append(len(set(expected[:k]) & set(actual[:k])) / k)
    return float(np.mean(values))


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark FAISS index accuracy and latency.")
    parser.add_argument("--vectors", type=Path, required=True, help=".npy embedding matrix")
    parser.add_argument("--queries", type=int, default=100)
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--tracking-uri", default="sqlite:///./mlflow.db")
    args = parser.parse_args()

    vectors = np.load(args.vectors).astype("float32")
    rng = np.random.default_rng(42)
    query_ids = rng.choice(len(vectors), size=min(args.queries, len(vectors)), replace=False)
    queries = vectors[query_ids]
    metadata = [{"row_id": i} for i in range(len(vectors))]

    exact = FaissVectorStore("flat")
    exact.build(vectors, metadata)
    reference = [[item["row_id"] for item in exact.search(query, args.top_k)] for query in queries]

    mlflow.set_tracking_uri(args.tracking_uri)
    mlflow.set_experiment("factorylens-faiss-benchmarks")
    for index_type in ("flat", "hnsw", "ivf"):
        store = FaissVectorStore(index_type)
        start = time.perf_counter()
        store.build(vectors, metadata)
        build_seconds = time.perf_counter() - start
        results, latencies = [], []
        for query in queries:
            started = time.perf_counter()
            found = store.search(query, args.top_k)
            latencies.append((time.perf_counter() - started) * 1000)
            results.append([item["row_id"] for item in found])
        with mlflow.start_run(run_name=index_type):
            mlflow.log_params(
                {
                    "index_type": index_type,
                    "vectors": len(vectors),
                    "dimension": vectors.shape[1],
                    "queries": len(queries),
                    "top_k": args.top_k,
                    "backend": store.backend,
                }
            )
            mlflow.log_metrics(
                {
                    "recall_at_k": recall_at_k(reference, results, args.top_k),
                    "mean_latency_ms": float(np.mean(latencies)),
                    "p95_latency_ms": float(np.percentile(latencies, 95)),
                    "build_seconds": build_seconds,
                }
            )
        print(index_type, np.mean(latencies), "ms")


if __name__ == "__main__":
    main()
