"""Daft UDFs for the vision pipeline."""

from __future__ import annotations

from typing import Any

import daft
import numpy as np
import structlog
from daft import DataType, Series
from numpy.typing import NDArray

logger = structlog.get_logger(__name__)


@daft.udf(return_dtype=DataType.python())
def download_images_udf(
    storage_paths: Series,
    record_ids: Series,
    *,
    bucket: str,
    prefix: str,
    endpoint_url: str | None,
) -> list[NDArray[np.uint8] | None]:
    """Download raw images from the image store (S3)."""
    import boto3
    import cv2

    kwargs = {"region_name": "eu-west-1"}
    if endpoint_url:
        kwargs["endpoint_url"] = endpoint_url

    client = boto3.client("s3", **kwargs)
    results: list[NDArray[np.uint8] | None] = []

    for storage_path, record_id in zip(
        storage_paths.to_pylist(), record_ids.to_pylist()
    ):
        if storage_path is None:
            results.append(None)
            continue

        try:
            if storage_path.startswith("s3://"):
                parts = storage_path[5:].split("/", 1)
                s3_bucket, key = parts[0], parts[1] if len(parts) > 1 else ""
            else:
                s3_bucket = bucket
                key = f"{prefix}/{storage_path}".strip("/")

            response = client.get_object(Bucket=s3_bucket, Key=key)
            raw_bytes = response["Body"].read()

            nparr = np.frombuffer(raw_bytes, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if image is None:
                logger.warning("image_decode_failed", record_id=record_id)

            results.append(image)

        except Exception as exc:
            logger.warning(
                "image_download_failed", record_id=record_id, error=str(exc)
            )
            results.append(None)

    return results


@daft.udf(return_dtype=DataType.python())
def run_inference_udf(
    images: Series,
    record_ids: Series,
    *,
    artifact_bucket: str,
    artifact_prefix: str,
    artifact_endpoint_url: str | None,
    model_name: str,
) -> list[dict[str, Any]]:
    """Run face inference via galadril-inference's InferenceEngine.

    One engine per Ray worker.
    """
    from galadril_inference import InferenceEngine, PredictionRequest
    from galadril_inference.storage import S3Loader

    loader = S3Loader(
        bucket=artifact_bucket,
        prefix=artifact_prefix,
        endpoint_url=artifact_endpoint_url,
    )

    engine = InferenceEngine(loader=loader)
    engine.load_model(model_name)

    results: list[dict[str, Any]] = []

    for image, record_id in zip(images.to_pylist(), record_ids.to_pylist()):
        if image is None:
            results.append({"record_id": record_id, "faces": [], "error": None})
            continue

        try:
            result = engine.predict(
                PredictionRequest(
                    model_name=model_name,
                    features={"action": "embed", "image": image},
                )
            )

            results.append(
                {
                    "record_id": record_id,
                    "faces": result.prediction.get("faces", []),
                    "model_version": result.model_version,
                    "inference_latency_ms": result.latency_ms,
                    "confidence": result.confidence,
                    "error": None,
                }
            )

        except Exception as exc:
            logger.warning(
                "inference_failed", record_id=record_id, error=str(exc)
            )
            results.append(
                {
                    "record_id": record_id,
                    "faces": [],
                    "error": str(exc),
                }
            )

    return results
