"""ChromaDB wrapper. One collection per RAG tool."""
import asyncio
import chromadb
from app.llm import embed
from app.config import settings

_client = chromadb.PersistentClient(path=settings.CHROMA_DIR)


def collection(name: str):
    return _client.get_or_create_collection(name)


async def rag_query(collection_name: str, text: str, k: int = 4) -> list[str]:
    """Embed the query, fetch the k nearest chunks. Returns [] if empty."""
    vec = await embed(text)
    coll = collection(collection_name)
    # chroma's query is sync + fast; run it off the event loop.
    res = await asyncio.to_thread(
        coll.query, query_embeddings=[vec], n_results=k
    )
    docs = res.get("documents") or [[]]
    return docs[0]


def add_documents(collection_name: str, ids: list[str],
                  docs: list[str], embeddings: list[list[float]]):
    coll = collection(collection_name)
    coll.upsert(ids=ids, documents=docs, embeddings=embeddings)
