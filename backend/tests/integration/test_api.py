# backend/tests/integration/test_api.py
import pytest
from fastapi.testclient import TestClient

def test_health_check(client):
    """Test health endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_root_endpoint(client):
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data

# Testy dla users endpoints (gdy je stworzysz)
def test_register_user(client, sample_user):
    """Test user registration"""
    response = client.post("/api/v1/users/register", json=sample_user)
    # assert response.status_code == 201
    # assert response.json()["username"] == sample_user["username"]

def test_register_duplicate_user(client, sample_user):
    """Test registering duplicate user"""
    # First registration
    client.post("/api/v1/users/register", json=sample_user)
    
    # Duplicate registration
    response = client.post("/api/v1/users/register", json=sample_user)
    # assert response.status_code == 400
    # assert "already exists" in response.json()["message"]

# Testy dla characters endpoints
def test_create_character_unauthorized(client, sample_character):
    """Test creating character without auth"""
    response = client.post("/api/v1/characters/", json=sample_character)
    # assert response.status_code == 401

def test_list_characters_empty(client):
    """Test listing characters when none exist"""
    response = client.get("/api/v1/characters/")
    # assert response.status_code == 200
    # assert response.json() == []