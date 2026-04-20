"""Unit tests for the ModelLoader — S3 fetches mocked with moto."""

import pickle

import boto3
import pytest
from moto import mock_aws
from unittest.mock import patch

from src.model_loader import ModelLoader


def _make_dummy_model():
    """Return a minimal sklearn-like model stub."""
    import numpy as np

    class DummyModel:
        def predict(self, x):
            return np.array([1.0])

    return DummyModel()


@pytest.fixture()
def s3_bucket(aws_credentials):
    with mock_aws():
        s3 = boto3.client("s3", region_name="eu-west-2")
        s3.create_bucket(
            Bucket="test-model-store",
            CreateBucketConfiguration={"LocationConstraint": "eu-west-2"},
        )
        yield s3


@pytest.fixture()
def aws_credentials(monkeypatch):
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_SECURITY_TOKEN", "testing")
    monkeypatch.setenv("AWS_SESSION_TOKEN", "testing")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "eu-west-2")


@mock_aws
def test_load_fetches_model_from_s3(aws_credentials):
    s3 = boto3.client("s3", region_name="eu-west-2")
    s3.create_bucket(
        Bucket="test-model-store",
        CreateBucketConfiguration={"LocationConstraint": "eu-west-2"},
    )
    model_bytes = pickle.dumps(_make_dummy_model())
    s3.put_object(Bucket="test-model-store", Key="models/latest/model.pkl", Body=model_bytes)

    loader = ModelLoader(bucket="test-model-store", key="models/latest/model.pkl")
    assert not loader.is_loaded

    loader.load()

    assert loader.is_loaded


@mock_aws
def test_predict_returns_tuple(aws_credentials):
    s3 = boto3.client("s3", region_name="eu-west-2")
    s3.create_bucket(
        Bucket="test-model-store",
        CreateBucketConfiguration={"LocationConstraint": "eu-west-2"},
    )
    model_bytes = pickle.dumps(_make_dummy_model())
    s3.put_object(Bucket="test-model-store", Key="models/latest/model.pkl", Body=model_bytes)

    loader = ModelLoader(bucket="test-model-store", key="models/latest/model.pkl")
    loader.load()

    prediction, confidence = loader.predict([1.0, 2.0, 3.0])

    assert isinstance(prediction, float)
    assert confidence == 1.0


def test_predict_before_load_raises():
    loader = ModelLoader(bucket="b", key="k")
    with pytest.raises(RuntimeError, match="not loaded"):
        loader.predict([1.0])


@mock_aws
def test_load_retries_on_missing_key(aws_credentials):
    s3 = boto3.client("s3", region_name="eu-west-2")
    s3.create_bucket(
        Bucket="test-model-store",
        CreateBucketConfiguration={"LocationConstraint": "eu-west-2"},
    )
    loader = ModelLoader(bucket="test-model-store", key="does/not/exist.pkl")
    with pytest.raises(RuntimeError, match="Failed to load model"):
        loader.load()
