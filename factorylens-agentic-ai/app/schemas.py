from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class Prediction(BaseModel):
    predicted_class: str
    confidence: float = Field(ge=0.0, le=1.0)
    probabilities: dict[str, float]
    model_version: str
    model_status: str
    embedding_dimension: int


class SimilarIncident(BaseModel):
    score: float
    image_path: str | None = None
    label: str | None = None
    incident_id: str | None = None
    machine_id: str | None = None
    resolution: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ManualEvidence(BaseModel):
    score: float
    heading: str
    text: str


class RiskAssessment(BaseModel):
    level: str
    score: int = Field(ge=0, le=100)
    reasons: list[str]


class WorkOrderResult(BaseModel):
    id: str
    priority: str
    status: str
    approved_by: str


class AnalysisResponse(BaseModel):
    incident_id: str
    machine_id: str
    prediction: Prediction
    similar_incidents: list[SimilarIncident]
    manual_evidence: list[ManualEvidence]
    risk: RiskAssessment
    probable_causes: list[str]
    recommended_actions: list[str]
    narrative: str
    work_order: WorkOrderResult | None = None
    human_approval_required: bool = True


class IncidentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    machine_id: str
    image_path: str
    predicted_class: str
    confidence: float
    risk_level: str
    symptoms: str
    status: str
    model_version: str
    created_at: datetime


class WorkOrderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    incident_id: str
    machine_id: str
    priority: str
    status: str
    approved_by: str
    created_at: datetime


class IndexInfo(BaseModel):
    backend: str
    index_type: str
    dimension: int | None
    vectors: int
    ready: bool
    metadata_path: str
