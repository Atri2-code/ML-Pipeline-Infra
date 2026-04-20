"""
Model loader — fetches a pickled model artefact from S3 and caches it
in memory. Retries on transient S3 errors with exponential backoff.
"""

import io
import logging
import pickle
import time
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
BACKOFF_BASE = 2.0


class ModelLoader:
    def __init__(self, bucket: str, key: str):
        self.bucket = bucket
        self.key = key
        self._model: Any = None
        self._s3 = boto3.client("s3")

    @property
    def is_loaded(self) -> bool:
        return self._model is not None

    def load(self) -> None:
        """Fetch model artefact from S3 with retry and exponential backoff."""
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                logger.info(
                    "Fetching model (attempt %d/%d): s3://%s/%s",
                    attempt, MAX_RETRIES, self.bucket, self.key,
                )
                response = self._s3.get_object(Bucket=self.bucket, Key=self.key)
                body = response["Body"].read()
                self._model = pickle.loads(body)  # noqa: S301
                logger.info("Model loaded successfully (%d bytes)", len(body))
                return
            except (BotoCoreError, ClientError) as exc:
                logger.warning("S3 fetch failed: %s", exc)
                if attempt == MAX_RETRIES:
                    raise RuntimeError(
                        f"Failed to load model after {MAX_RETRIES} attempts"
                    ) from exc
                sleep = BACKOFF_BASE ** attempt
                logger.info("Retrying in %.1fs", sleep)
                time.sleep(sleep)

    def predict(self, features: list[float]) -> tuple[float, float]:
        """
        Run inference. Returns (prediction, confidence).
        Raises ValueError on dimension mismatch.
        """
        if not self.is_loaded:
            raise RuntimeError("Model not loaded — call load() first")

        import numpy as np  # lazy import — not needed at module load time

        x = np.array(features).reshape(1, -1)

        if hasattr(self._model, "predict_proba"):
            proba = self._model.predict_proba(x)[0]
            prediction = float(proba.argmax())
            confidence = float(proba.max())
        elif hasattr(self._model, "predict"):
            prediction = float(self._model.predict(x)[0])
            confidence = 1.0
        else:
            raise ValueError("Model does not implement predict or predict_proba")

        return prediction, confidence
