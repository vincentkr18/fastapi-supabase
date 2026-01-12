"""
Basic tests for the FastAPI application.
"""
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_root_endpoint():
    """Test root endpoint returns health status."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "healthy"


def test_health_check():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_list_plans_unauthenticated():
    """Test that plans endpoint is public."""
    response = client.get("/plans")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_profile_unauthorized():
    """Test that profile endpoint requires authentication."""
    response = client.get("/users/me")
    assert response.status_code == 401


def test_get_subscriptions_unauthorized():
    """Test that subscriptions endpoint requires authentication."""
    response = client.get("/subscriptions/me")
    assert response.status_code == 401


def test_create_api_key_unauthorized():
    """Test that API key creation requires authentication."""
    response = client.post("/api-keys", json={"name": "Test Key"})
    assert response.status_code == 401
