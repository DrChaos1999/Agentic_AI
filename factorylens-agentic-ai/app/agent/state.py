from __future__ import annotations

from typing import Any, TypedDict


class AgentState(TypedDict, total=False):
    image_path: str
    machine_id: str
    symptoms: str
    criticality: str
    approve_work_order: bool
    approved_by: str
    top_k: int

    prediction: dict[str, Any]
    embedding: list[float]
    similar_incidents: list[dict[str, Any]]
    manual_evidence: list[dict[str, Any]]
    risk: dict[str, Any]
    probable_causes: list[str]
    recommended_actions: list[str]
    narrative: str
    incident_id: str
    work_order: dict[str, Any] | None
