
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "message": "HireSignal API is running smoothly."}

def test_screen_no_resumes():
    response = client.post("/screen", data={"job_description": "We need a Python developer."})
    assert response.status_code == 422 # FastAPI validation error for missing files
