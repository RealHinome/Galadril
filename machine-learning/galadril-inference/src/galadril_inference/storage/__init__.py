"""Artifact loading backends."""

from galadril_inference.storage.local import LocalLoader
from galadril_inference.storage.s3 import S3Loader

__all__ = ["LocalLoader", "S3Loader"]
