from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agent.graph import FactoryLensAgent
from app.api.deps import get_runtime
from app.db.models import Incident, WorkOrder
from app.db.session import get_db
from app.schemas import (
    AnalysisResponse,
    IncidentRead,
    IndexInfo,
    Prediction,
    SimilarIncident,
    WorkOrderRead,
)
from app.services.runtime import RuntimeServices
from app.utils.files import save_validated_upload

router = APIRouter()


@router.get("/health")
def health(runtime: RuntimeServices = Depends(get_runtime)) -> dict[str, object]:
    return {
        "status": "ok",
        "app": runtime.settings.app_name,
        "model": runtime.vision.info(),
        "image_index_ready": runtime.image_store.ready,
        "image_index_vectors": runtime.image_store.size,
    }


@router.get("/model")
def model_info(runtime: RuntimeServices = Depends(get_runtime)) -> dict[str, object]:
    return runtime.vision.info()


@router.get("/index", response_model=IndexInfo)
def index_info(runtime: RuntimeServices = Depends(get_runtime)) -> IndexInfo:
    return IndexInfo(
        backend=runtime.image_store.backend,
        index_type=runtime.image_store.index_type,
        dimension=runtime.image_store.dimension,
        vectors=runtime.image_store.size,
        ready=runtime.image_store.ready,
        metadata_path=str(runtime.settings.faiss_metadata_path),
    )


@router.post("/predict", response_model=Prediction)
def predict(
    image: UploadFile = File(...),
    runtime: RuntimeServices = Depends(get_runtime),
) -> Prediction:
    path = save_validated_upload(image, runtime.settings.upload_dir, runtime.settings.max_upload_mb)
    output = runtime.vision.predict_path(path)
    return Prediction(
        predicted_class=output.predicted_class,
        confidence=output.confidence,
        probabilities=output.probabilities,
        model_version=output.model_version,
        model_status=output.model_status,
        embedding_dimension=int(output.embedding.shape[0]),
    )


@router.post("/search", response_model=list[SimilarIncident])
def search_similar(
    image: UploadFile = File(...),
    top_k: int = Form(5, ge=1, le=50),
    runtime: RuntimeServices = Depends(get_runtime),
) -> list[SimilarIncident]:
    path = save_validated_upload(image, runtime.settings.upload_dir, runtime.settings.max_upload_mb)
    output = runtime.vision.predict_path(path)
    if runtime.image_store.dimension is not None and output.embedding.shape[0] != runtime.image_store.dimension:
        raise HTTPException(
            status_code=409,
            detail="The loaded model embedding dimension does not match the saved FAISS index. Rebuild the index.",
        )
    return [SimilarIncident(**item) for item in runtime.image_store.search(output.embedding, top_k)]


@router.post("/analyze", response_model=AnalysisResponse)
def analyze(
    image: UploadFile = File(...),
    machine_id: str = Form(..., min_length=1, max_length=100),
    symptoms: str = Form("", max_length=2000),
    criticality: str = Form("medium", pattern="^(low|medium|high|critical)$"),
    top_k: int = Form(5, ge=1, le=50),
    approve_work_order: bool = Form(False),
    approved_by: str = Form("human-operator", max_length=100),
    runtime: RuntimeServices = Depends(get_runtime),
    db: Session = Depends(get_db),
) -> AnalysisResponse:
    path = save_validated_upload(image, runtime.settings.upload_dir, runtime.settings.max_upload_mb)
    agent = FactoryLensAgent(runtime.settings, runtime.vision, runtime.image_store, runtime.manual_store, db)
    state = agent.run(
        {
            "image_path": str(path),
            "machine_id": machine_id,
            "symptoms": symptoms,
            "criticality": criticality,
            "top_k": top_k,
            "approve_work_order": approve_work_order,
            "approved_by": approved_by,
        }
    )
    return AnalysisResponse(
        incident_id=state["incident_id"],
        machine_id=machine_id,
        prediction=state["prediction"],
        similar_incidents=state.get("similar_incidents", []),
        manual_evidence=state.get("manual_evidence", []),
        risk=state["risk"],
        probable_causes=state["probable_causes"],
        recommended_actions=state["recommended_actions"],
        narrative=state["narrative"],
        work_order=state.get("work_order"),
        human_approval_required=not approve_work_order,
    )


@router.get("/incidents", response_model=list[IncidentRead])
def list_incidents(
    limit: int = 50,
    db: Session = Depends(get_db),
) -> list[Incident]:
    limit = min(max(limit, 1), 500)
    return list(db.scalars(select(Incident).order_by(Incident.created_at.desc()).limit(limit)))


@router.get("/work-orders", response_model=list[WorkOrderRead])
def list_work_orders(
    limit: int = 50,
    db: Session = Depends(get_db),
) -> list[WorkOrder]:
    limit = min(max(limit, 1), 500)
    return list(db.scalars(select(WorkOrder).order_by(WorkOrder.created_at.desc()).limit(limit)))
