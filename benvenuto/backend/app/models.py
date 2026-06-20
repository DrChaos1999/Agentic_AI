"""Pydantic request/response schemas."""
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str
    history: list[dict] = Field(default_factory=list)


class VisionRequest(BaseModel):
    image_b64: str
    question: str = "What is in this image? Explain it for an international student in Italy."


class SpeakRequest(BaseModel):
    text: str
    voice: str = "alloy"
