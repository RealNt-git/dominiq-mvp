###backend/tests/test_api/test_auth.py
import pytest
from fastapi import status

@pytest.mark.api
def test_login_success(client):
    """Тест успешной авторизации"""
    response = client.post("/api/auth/login", json={"email": "newuser@example.com"})
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert "id" in data
    assert "total_xp" in data

@pytest.mark.api
def test_login_invalid_email(client):
    """Тест с невалидным email"""
    response = client.post("/api/auth/login", json={"email": "not-an-email"})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

@pytest.mark.api
def test_me_endpoint(client, auth_headers):
    """Тест получения профиля текущего пользователя"""
    response = client.get("/api/auth/me", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["email"] == auth_headers["X-User-Email"]