# -*- coding: utf-8 -*-
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_get_index():
    response = client.get("/")
    assert response.status_code == 200
    assert "RAG-валидатор" in response.text

def test_post_validate_arch():
    payload = {
        "text": "Класс UserService содержит методы регистрации и прямого выполнения SQL-запросов к БД без репозитория."
    }
    response = client.post("/validate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "violations" in data
    assert "sources" in data
    assert "refused" in data

def test_post_validate_empty():
    response = client.post("/validate", json={"text": ""})
    assert response.status_code in (200, 422)
