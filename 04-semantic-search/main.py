"""Semantic search vs keyword search, side by side (OpenAI embeddings).

Embeddings map text to vectors where similar meanings are close together.
Chroma calls OpenAI's text-embedding-3-small for both indexing and queries;
we add a naive keyword matcher so the difference is visible.
"""
import os

import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

load_dotenv()

MOVIES = [
    ("Interstellar", "Astronauts travel through a wormhole seeking a new home for humanity while a father fights to return to his daughter."),
    ("Finding Nemo", "A timid clownfish crosses the ocean to rescue his son, learning courage along the way."),
    ("The Martian", "A stranded astronaut survives alone on Mars using science, humor and potatoes."),
    ("Up", "An old widower ties balloons to his house and flies to South America, finding new family in a young scout."),
    ("Gravity", "Two astronauts fight to survive after debris destroys their shuttle in orbit."),
    ("Ratatouille", "A rat with a gift for cooking secretly runs a Paris restaurant kitchen."),
    ("WALL-E", "A lonely waste-collecting robot on an abandoned Earth falls in love and follows her into space."),
    ("Whiplash", "A young drummer pushes himself to the edge under a ruthless music teacher."),
    ("Spirited Away", "A girl enters a spirit world and works in a bathhouse to free her parents from a curse."),
    ("Moneyball", "A baseball manager uses statistics to build a winning team on a tiny budget."),
    ("Coco", "A boy journeys into the Land of the Dead to uncover his family's musical past."),
    ("Arrival", "A linguist decodes an alien language and discovers it changes how she experiences time."),
]

openai_ef = embedding_functions.OpenAIEmbeddingFunction(
    api_key=os.getenv("OPENAI_API_KEY"),
    model_name="text-embedding-3-small",
)
chroma = chromadb.Client()  # in-memory is fine for a demo
collection = chroma.get_or_create_collection("movies", embedding_function=openai_ef)
collection.add(
    ids=[str(i) for i in range(len(MOVIES))],
    documents=[f"{t}: {d}" for t, d in MOVIES],
    metadatas=[{"title": t} for t, _ in MOVIES],
)

app = FastAPI()


class Query(BaseModel):
    query: str


def keyword_search(query: str, k: int = 4):
    """Naive keyword scoring: count how many query words appear."""
    words = set(query.lower().split())
    scored = []
    for title, desc in MOVIES:
        text = f"{title} {desc}".lower()
        hits = sum(1 for w in words if w in text)
        if hits:
            scored.append({"title": title, "desc": desc, "score": hits})
    return sorted(scored, key=lambda m: -m["score"])[:k]


@app.post("/api/search")
def search(q: Query):
    res = collection.query(query_texts=[q.query], n_results=4)
    semantic = [
        {
            "title": m["title"],
            "desc": d.split(": ", 1)[1],
            # Chroma returns distance (lower = closer); convert to a rough
            # similarity score for display.
            "score": round(1 / (1 + dist), 3),
        }
        for d, m, dist in zip(res["documents"][0], res["metadatas"][0], res["distances"][0])
    ]
    return {"semantic": semantic, "keyword": keyword_search(q.query)}


app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
