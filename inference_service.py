"""
ML inference service — FastAPI endpoint wrapping a pickled sklearn model.
Loads the model artefact from S3 on startup and caches it in memory.
"""

import logging
import os
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from model_loader import ModelLoader

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

MODEL_BUCKET = os.environ["MODEL_BUCKET"]
MODEL_KEY = os.getenv("MODEL_KEY", "models/latest/model.pkl")

model_loader: ModelLoader | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global model_loader
    logger.info("Loading model from s3://%s/%s", MODEL_BUCKET, MODEL_KEY)
    model_loader = ModelLoader(bucket=MODEL_BUCKET, key=MODEL_KEY)
    model_loader.load()
    logger.info("Model loaded — service ready")
    yield
    logger.info("Shutting down inference service")


app = FastAPI(
    title="ML Inference Service",
    description="Production inference endpoint for ML Pipeline Infrastructure",
    version="1.0.0",
    lifespan=lifespan,
)


class InferenceRequest(BaseModel):
    features: list[float] = Field(..., min_length=1, description="Feature vector")


class InferenceResponse(BaseModel):
    prediction: float
    confidence: float
    latency_ms: float


@app.get("/healthz")
def liveness():
    return {"status": "ok"}


@app.get("/ready")
def readiness():
    if model_loader is None or not model_loader.is_loaded:
        raise HTTPException(status_code=503, detail="Model not loaded")
    return {"status": "ready"}


@app.post("/predict", response_model=InferenceResponse)
def predict(request: InferenceRequest):
    if model_loader is None or not model_loader.is_loaded:
        raise HTTPException(status_code=503, detail="Model not available")

    t0 = time.perf_counter()
    try:
        prediction, confidence = model_loader.predict(request.features)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    latency_ms = (time.perf_counter() - t0) * 1000
    logger.info("Prediction complete in %.2fms", latency_ms)

    return InferenceResponse(
        prediction=prediction,
        confidence=confidence,
        latency_ms=round(latency_ms, 2),
    )


@app.get("/metrics")
def metrics():
    """Minimal Prometheus-compatible metrics endpoint."""
    return {
        "model_loaded": model_loader is not None and model_loader.is_loaded,
        "model_key": MODEL_KEY,
    }
