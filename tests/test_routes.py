from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    assert client.get("/api/health").status_code == 200


def test_unstick_degrades_without_ollama():
    response = client.post("/api/unstick", json={"goal": "start a portfolio", "minutes": 5, "energy": 2, "location": "home", "time": "21:30"})
    assert response.status_code == 200
    data = response.json()
    assert data["start_here"]["constraints"]["passes"] is True
    assert data["not_today"]["message"]
