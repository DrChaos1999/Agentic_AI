from fastapi.testclient import TestClient

from app.main import app


def test_root_and_health():
    with TestClient(app) as client:
        root = client.get("/")
        assert root.status_code == 200
        health = client.get("/api/v1/health")
        assert health.status_code == 200
        assert health.json()["status"] == "ok"


def test_analyze_runs_agent_workflow_without_creating_work_order():
    image_path = "data/demo/crack/crack_00.png"
    with TestClient(app) as client, open(image_path, "rb") as image:
        response = client.post(
            "/api/v1/analyze",
            files={"image": ("crack.png", image, "image/png")},
            data={
                "machine_id": "MOTOR-04",
                "symptoms": "overheating and unusual vibration",
                "criticality": "high",
                "top_k": "3",
                "approve_work_order": "false",
            },
        )
    assert response.status_code == 200
    payload = response.json()
    assert payload["incident_id"]
    assert payload["prediction"]["model_status"] == "demo-untrained-do-not-use-for-production"
    assert len(payload["similar_incidents"]) == 3
    assert payload["manual_evidence"]
    assert payload["risk"]["level"] in {"low", "medium", "high", "critical"}
    assert payload["work_order"] is None
    assert payload["human_approval_required"] is True
