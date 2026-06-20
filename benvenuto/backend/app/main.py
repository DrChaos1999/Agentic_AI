"""FastAPI app: streaming /chat plus voice, vision, and TTS endpoints."""
import base64
import json
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, Response

from app.config import settings
from app.models import ChatRequest, VisionRequest, SpeakRequest
from app.agent import stream_agent
from app.llm import transcribe, speak, describe_image, moderate

app = FastAPI(title="Benvenuto API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/chat")
async def chat(req: ChatRequest):
    async def gen():
        async for evt in stream_agent(req.message, req.history):
            yield f"data: {json.dumps(evt, ensure_ascii=False)}\n\n"
        yield "data: {\"type\": \"done\"}\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream")


@app.post("/voice")
async def voice(file: UploadFile = File(...)):
    audio = await file.read()
    transcript = await transcribe(audio, file.filename or "audio.webm")
    # Collect the streamed answer into a single string for the voice flow.
    answer, tools = "", []
    async for evt in stream_agent(transcript, []):
        if evt["type"] == "token":
            answer += evt["text"]
        elif evt["type"] == "tools":
            tools += evt["tools"]
    return {"transcript": transcript, "answer": answer, "tools_used": tools}


@app.post("/vision")
async def vision(req: VisionRequest):
    if await moderate(req.question):
        return {"answer": "I can't help with that request."}
    answer = await describe_image(req.image_b64, req.question)
    return {"answer": answer}


@app.post("/speak")
async def speak_endpoint(req: SpeakRequest):
    audio = await speak(req.text, req.voice)
    return Response(content=audio, media_type="audio/mpeg")
