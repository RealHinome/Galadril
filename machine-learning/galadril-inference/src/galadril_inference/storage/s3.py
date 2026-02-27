"""S3 artifact loader for production environments.

Downloads model artifacts from S3 into a local cache directory, then returns
the cached path.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

import structlog

from galadril_inference.common.exceptions import ArtifactResolutionError
from galadril_inference.loading.loader import ArtifactLoader

if TYPE_CHECKING:
    from mypy_boto3_s3.client import S3Client

logger = structlog.get_logger(__name__)

_DEFAULT_CACHE_DIR = Path(tempfile.gettempdir()) / "galadril_artifact_cache"


class S3Loader(ArtifactLoader):
    """Download and cache model artifacts from S3."""

    def __init__(
        self,
        bucket: str,
        prefix: str = "",
        *,
        s3_client: S3Client | None = None,
        cache_dir: str | Path | None = None,
        endpoint_url: str | None = None,
    ) -> None:
        self._bucket = bucket
        self._prefix = prefix.strip("/")
        self._cache_dir = Path(
            cache_dir
            or os.environ.get(
                "GALADRIL_ARTIFACT_CACHE",
                str(_DEFAULT_CACHE_DIR),
            ),
        ).resolve()
        self._client = s3_client or self._default_client(endpoint_url)

        self._cache_dir.mkdir(parents=True, exist_ok=True)
        logger.info(
            "loader_initialized",
            bucket=self._bucket,
            prefix=self._prefix or "(root)",
            cache_path=str(self._cache_dir),
        )

    def resolve(self, model_name: str, version: str) -> str:
        """
        Download artifacts from S3 (if not cached) and return the local
        path.
        """
        cached_path = self._cached_path(model_name, version)

        if self._is_cache_valid(cached_path):
            logger.debug(
                "cache_hit",
                name=model_name,
                version=version,
                path=str(cached_path),
            )
            return str(cached_path)

        s3_prefix = self._s3_key(model_name, version)
        objects = self._list_objects(s3_prefix)

        if not objects:
            raise ArtifactResolutionError(
                model_name=model_name,
                version=version,
                backend=repr(self),
            )

        self._download_artifacts(
            objects=objects,
            s3_prefix=s3_prefix,
            dest=cached_path,
        )

        logger.info(
            "artifacts_downloaded",
            name=model_name,
            version=version,
            file_count=len(objects),
            path=str(cached_path),
        )
        return str(cached_path)

    def exists(self, model_name: str, version: str) -> bool:
        """Check whether artifacts exist in S3 for this model + version."""
        s3_prefix = self._s3_key(model_name, version)
        return len(self._list_objects(s3_prefix)) > 0

    def invalidate_cache(self, model_name: str, version: str) -> None:
        """Remove cached artifacts so the next resolve() re-downloads them."""
        cached_path = self._cached_path(model_name, version)
        if cached_path.exists():
            shutil.rmtree(cached_path)
            logger.info("cache_invalidated", name=model_name, version=version)

    def _list_objects(self, prefix: str) -> list[str]:
        """Return all S3 object keys under the given prefix."""
        keys: list[str] = []
        paginator = self._client.get_paginator("list_objects_v2")

        for page in paginator.paginate(Bucket=self._bucket, Prefix=prefix):
            for obj in page.get("Contents", []):
                key = obj["Key"]
                if not key.endswith("/"):
                    keys.append(key)

        return keys

    def _download_artifacts(
        self,
        objects: list[str],
        s3_prefix: str,
        dest: Path,
    ) -> None:
        """Download a list of S3 objects into a local directory."""
        tmp_dir = dest.with_suffix(".tmp")

        if tmp_dir.exists():
            shutil.rmtree(tmp_dir)
        if dest.exists():
            shutil.rmtree(dest)

        tmp_dir.mkdir(parents=True)

        try:
            for key in objects:
                relative = key[len(s3_prefix) :].lstrip("/")
                local_file = tmp_dir / relative

                local_file.parent.mkdir(parents=True, exist_ok=True)
                self._client.download_file(self._bucket, key, str(local_file))

                logger.debug("file_downloaded", bucket=self._bucket, key=key)

            tmp_dir.rename(dest)

        except Exception:
            if tmp_dir.exists():
                shutil.rmtree(tmp_dir)
            raise

    def _s3_key(self, model_name: str, version: str) -> str:
        """Build the full S3 key prefix for a model version."""
        parts = [self._prefix, model_name, version]
        return "/".join(p for p in parts if p) + "/"

    def _cached_path(self, model_name: str, version: str) -> Path:
        """Build a deterministic local cache path."""
        source_id = hashlib.sha256(
            f"{self._bucket}:{self._prefix}".encode(),
        ).hexdigest()[:12]

        return self._cache_dir / source_id / model_name / version

    @staticmethod
    def _is_cache_valid(path: Path) -> bool:
        """A cache entry is valid if it exists and is non-empty."""
        return path.is_dir() and any(path.iterdir())

    @staticmethod
    def _default_client(endpoint_url: str | None = None) -> S3Client:
        """Create a boto3 S3 client with default credential chain."""
        import boto3

        kwargs: dict = {}
        if endpoint_url:
            kwargs["endpoint_url"] = endpoint_url

        return boto3.client("s3", **kwargs)

    def __repr__(self) -> str:
        return (
            f"<S3Loader bucket={self._bucket!r} "
            f"prefix={self._prefix!r} "
            f"cache={str(self._cache_dir)!r}>"
        )
