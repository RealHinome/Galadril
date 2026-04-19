"""Daft UDFs for the vision pipeline."""

from __future__ import annotations

from typing import Any, cast

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
    """Download raw images from the image store (S3) across Ray workers."""
    import boto3
    import cv2

    client = boto3.client(
        "s3", region_name="eu-west-1", endpoint_url=endpoint_url
    )
    results: list[NDArray[np.uint8] | None] = []

    for storage_path, record_id in zip(
        storage_paths.to_pylist(), record_ids.to_pylist()
    ):
        if not storage_path:
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
            nparr = np.frombuffer(response["Body"].read(), np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if image is None:
                logger.warning("image_decode_failed", record_id=record_id)

            results.append(cast(NDArray[np.uint8], image))
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
    action: str = "embed",
) -> list[dict[str, Any]]:
    """Generic inference UDF running on Ray workers."""
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
            results.append({"record_id": record_id, "error": "No image data"})
            continue

        try:
            req = PredictionRequest(
                model_name=model_name,
                features={"action": action, "image": image},
            )
            result = engine.predict(req)
            results.append(
                {
                    "record_id": record_id,
                    "prediction": result.prediction,
                    "confidence": result.confidence,
                    "model_version": result.model_version,
                    "error": None,
                }
            )
        except Exception as exc:
            logger.warning(
                "inference_failed", record_id=record_id, error=str(exc)
            )
            results.append({"record_id": record_id, "error": str(exc)})

    return results
