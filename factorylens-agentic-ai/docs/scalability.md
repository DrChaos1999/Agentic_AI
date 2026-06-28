# Scalability plan

## Local portfolio version

- FastAPI and Streamlit on one machine
- SQLite metadata
- local image storage
- FAISS `IndexFlatIP`
- local MLflow SQLite backend

## Team deployment

- PostgreSQL for incidents, work orders and MLflow metadata
- S3 or MinIO for images, checkpoints and MLflow artifacts
- Redis plus Celery/RQ for asynchronous embedding and index updates
- dedicated GPU inference workers
- FAISS HNSW for low-latency approximate search
- immutable index snapshots with atomic active-index switching

## Large collections

Partition indexes by factory, product family or machine type. Route a query to the smallest relevant shard. New vectors enter a small delta index; a background job periodically compacts the delta into a rebuilt main index. Keep the previous snapshot for rollback.

Measure recall@K, mean and P95 latency, memory, build time and index size with `training/benchmark_faiss.py`, logging all values to MLflow.
