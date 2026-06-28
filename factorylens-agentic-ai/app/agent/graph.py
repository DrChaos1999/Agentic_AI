from __future__ import annotations

import json
from typing import Any

from sqlalchemy.orm import Session

from app.agent.llm_composer import LLMComposer
from app.agent.recommendations import recommendations_for
from app.agent.risk import calculate_risk
from app.agent.state import AgentState
from app.core.config import Settings
from app.db.models import Incident, WorkOrder
from app.retrieval.faiss_store import FaissVectorStore
from app.retrieval.manual_store import ManualFaissStore
from app.vision.service import VisionService

try:
    from langgraph.graph import END, START, StateGraph
except ImportError:  # pragma: no cover
    END = START = StateGraph = None


class FactoryLensAgent:
    """Stateful agentic workflow with deterministic tools and a human approval gate."""

    def __init__(
        self,
        settings: Settings,
        vision: VisionService,
        image_store: FaissVectorStore,
        manual_store: ManualFaissStore,
        db: Session,
    ) -> None:
        self.settings = settings
        self.vision = vision
        self.image_store = image_store
        self.manual_store = manual_store
        self.db = db
        self.llm = LLMComposer(settings)
        self.graph = self._build_graph() if StateGraph is not None else None

    def _build_graph(self):
        builder = StateGraph(AgentState)
        builder.add_node("classify", self._classify)
        builder.add_node("retrieve", self._retrieve)
        builder.add_node("manual", self._manual)
        builder.add_node("risk", self._risk)
        builder.add_node("recommend", self._recommend)
        builder.add_node("persist", self._persist)
        builder.add_node("work_order", self._work_order)
        builder.add_edge(START, "classify")
        builder.add_edge("classify", "retrieve")
        builder.add_edge("retrieve", "manual")
        builder.add_edge("manual", "risk")
        builder.add_edge("risk", "recommend")
        builder.add_edge("recommend", "persist")
        builder.add_conditional_edges(
            "persist",
            lambda state: "work_order" if state.get("approve_work_order") else "end",
            {"work_order": "work_order", "end": END},
        )
        builder.add_edge("work_order", END)
        return builder.compile()

    def run(self, initial: AgentState) -> AgentState:
        if self.graph is not None:
            return self.graph.invoke(initial)
        # Lightweight fallback preserves the same deterministic sequence.
        state: AgentState = dict(initial)
        for node in (self._classify, self._retrieve, self._manual, self._risk, self._recommend, self._persist):
            state.update(node(state))
        if state.get("approve_work_order"):
            state.update(self._work_order(state))
        return state

    def _classify(self, state: AgentState) -> dict[str, Any]:
        output = self.vision.predict_path(state["image_path"])
        return {
            "prediction": {
                "predicted_class": output.predicted_class,
                "confidence": output.confidence,
                "probabilities": output.probabilities,
                "model_version": output.model_version,
                "model_status": output.model_status,
                "embedding_dimension": int(output.embedding.shape[0]),
            },
            "embedding": output.embedding.tolist(),
        }

    def _retrieve(self, state: AgentState) -> dict[str, Any]:
        import numpy as np

        results = self.image_store.search(
            np.asarray(state["embedding"], dtype="float32"), top_k=state.get("top_k", 5)
        )
        return {"similar_incidents": results}

    def _manual(self, state: AgentState) -> dict[str, Any]:
        prediction = state["prediction"]
        query = (
            f"{prediction['predicted_class']} defect {state.get('symptoms', '')} "
            f"machine criticality {state.get('criticality', 'medium')}"
        )
        return {"manual_evidence": self.manual_store.search(query, top_k=3)}

    def _risk(self, state: AgentState) -> dict[str, Any]:
        prediction = state["prediction"]
        similar_failures = sum(
            1
            for item in state.get("similar_incidents", [])
            if item.get("label") == prediction["predicted_class"]
        )
        risk = calculate_risk(
            defect_class=prediction["predicted_class"],
            confidence=float(prediction["confidence"]),
            criticality=state.get("criticality", "medium"),
            symptoms=state.get("symptoms", ""),
            similar_failures=similar_failures,
        )
        return {"risk": risk.model_dump()}

    def _recommend(self, state: AgentState) -> dict[str, Any]:
        defect = state["prediction"]["predicted_class"]
        risk_level = state["risk"]["level"]
        causes, actions = recommendations_for(defect, risk_level)
        fallback = (
            f"FactoryLens detected '{defect}' with {state['prediction']['confidence']:.1%} confidence. "
            f"The deterministic risk tool rated this case {risk_level} ({state['risk']['score']}/100). "
            "Review the retrieved examples and manual evidence, then have a qualified operator verify "
            "the component before acting."
        )
        narrative = self.llm.compose(
            {
                "prediction": state["prediction"],
                "risk": state["risk"],
                "similar_incidents": state.get("similar_incidents", []),
                "manual_evidence": state.get("manual_evidence", []),
                "recommended_actions": actions,
            },
            fallback,
        )
        return {
            "probable_causes": causes,
            "recommended_actions": actions,
            "narrative": narrative,
        }

    def _persist(self, state: AgentState) -> dict[str, Any]:
        analysis = {
            key: state.get(key)
            for key in (
                "prediction",
                "similar_incidents",
                "manual_evidence",
                "risk",
                "probable_causes",
                "recommended_actions",
                "narrative",
            )
        }
        incident = Incident(
            machine_id=state["machine_id"],
            image_path=state["image_path"],
            predicted_class=state["prediction"]["predicted_class"],
            confidence=float(state["prediction"]["confidence"]),
            risk_level=state["risk"]["level"],
            symptoms=state.get("symptoms", ""),
            model_version=state["prediction"]["model_version"],
            analysis_json=json.dumps(analysis, ensure_ascii=False),
        )
        self.db.add(incident)
        self.db.commit()
        self.db.refresh(incident)
        return {"incident_id": incident.id, "work_order": None}

    def _work_order(self, state: AgentState) -> dict[str, Any]:
        order = WorkOrder(
            incident_id=state["incident_id"],
            machine_id=state["machine_id"],
            priority=state["risk"]["level"],
            actions_json=json.dumps(state["recommended_actions"], ensure_ascii=False),
            approved_by=state.get("approved_by", "human-operator"),
        )
        self.db.add(order)
        self.db.commit()
        self.db.refresh(order)
        return {
            "work_order": {
                "id": order.id,
                "priority": order.priority,
                "status": order.status,
                "approved_by": order.approved_by,
            }
        }
