"""Unit tests for the inference service FastAPI endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch


@pytest.fixture()
def mock_model_loader():
    loader = MagicMock()
    loader.is_loaded = True
    loader.predict.return_value = (1.0, 0.92)
    return loader


@pytest.fixture()
def client(mock_model_loader):
    with patch.dict("os.environ", {"MODEL_BUCKET": "test-bucket"}):
        import importlib
        import src.inference_service as svc

        importlib.reload(svc)
        svc.model_loader = mock_model_loader
        yield TestClient(svc.app)


def test_liveness(client):
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readiness_when_loaded(client):
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_readiness_when_not_loaded(client, mock_model_loader):
    mock_model_loader.is_loaded = False
    response = client.get("/ready")
    assert response.status_code == 503


def test_predict_returns_valid_schema(client):
    response = client.post("/predict", json={"features": [1.0, 2.0, 3.0]})
    assert response.status_code == 200
    data = response.json()
    assert "prediction" in data
    assert "confidence" in data
    assert "latency_ms" in data
    assert isinstance(data["latency_ms"], float)


def test_predict_confidence_in_range(client):
    response = client.post("/predict", json={"features": [0.5, 1.5]})
    assert response.status_code == 200
    assert 0.0 <= response.json()["confidence"] <= 1.0


def test_predict_when_model_unavailable(client, mock_model_loader):
    mock_model_loader.is_loaded = False
    response = client.post("/predict", json={"features": [1.0, 2.0]})
    assert response.status_code == 503


def test_predict_propagates_value_error(client, mock_model_loader):
    mock_model_loader.predict.side_effect = ValueError("dimension mismatch")
    response = client.post("/predict", json={"features": [1.0]})
    assert response.status_code == 422


def test_metrics_endpoint(client):
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "model_loaded" in response.json()
