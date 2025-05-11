from fastapi.testclient import TestClient
from packages.backend.app.main import app
from packages.backend.app.database import db
import pytest

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to PowerScaler Battle Arena"}

def test_battle_endpoint():
    test_battle = {
        "character1": "Superman",
        "character2": "Batman"
    }
    
    response = client.post("/battle", json=test_battle)
    assert response.status_code == 200
    data = response.json()
    
    assert "winner" in data
    assert "reasoning" in data
    assert "timestamp" in data
    assert data["winner"] in ["Superman", "Batman"]

def test_battle_history():
    response = client.get("/battle/history")
    assert response.status_code == 200
    data = response.json()
    
    assert isinstance(data, list)
    if data:
        assert all(key in data[0] for key in ["character1", "character2", "winner", "reasoning", "timestamp"]) 