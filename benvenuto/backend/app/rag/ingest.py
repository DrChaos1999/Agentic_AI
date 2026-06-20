"""Chunk every file in data/<topic>/, embed it, and seed ChromaDB.

Run once (and whenever you change data/):  python -m app.rag.ingest
"""
import asyncio
import hashlib
from pathlib import Path
from app.llm import embed
from app.rag.store import add_documents

DATA_DIR = Path(__file__).resolve().parents[2] / "data"

# folder name in data/  ->  chroma collection name
COLLECTIONS = {
    "law": "law",
    "cuisine": "cuisine",
    "tourism_traps": "tourism_traps",
    "etiquette": "etiquette",
    "scholarships": "scholarships",
}

CHUNK_SIZE = 900
CHUNK_OVERLAP = 150


def chunk(text: str) -> list[str]:
    text = text.strip()
    if len(text) <= CHUNK_SIZE:
        return [text] if text else []
    out, start = [], 0
    while start < len(text):
        end = start + CHUNK_SIZE
        out.append(text[start:end])
        start = end - CHUNK_OVERLAP
    return out


async def ingest_folder(folder: str, collection_name: str):
    path = DATA_DIR / folder
    if not path.exists():
        print(f"[ingest] {folder:<14}-> (no folder, skipped)")
        return
    ids, docs, vecs = [], [], []
    for file in sorted(path.glob("**/*")):
        if file.suffix.lower() not in {".md", ".txt"}:
            continue
        for i, c in enumerate(chunk(file.read_text(encoding="utf-8"))):
            uid = hashlib.md5(f"{file.name}:{i}".encode()).hexdigest()
            ids.append(uid)
            docs.append(c)
            vecs.append(await embed(c))
    if docs:
        add_documents(collection_name, ids, docs, vecs)
    print(f"[ingest] {folder:<14}-> {len(docs)} chunks embedded")


async def main():
    for folder, name in COLLECTIONS.items():
        await ingest_folder(folder, name)
    print("ChromaDB seeded at", DATA_DIR.parent / "chroma_db")


if __name__ == "__main__":
    asyncio.run(main())
