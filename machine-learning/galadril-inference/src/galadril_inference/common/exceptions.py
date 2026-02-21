"""Exception hierarchy for inferences."""


class GaladrilInferenceError(Exception):
    """Base exception for all inference-related errors."""


class ModelNotFoundError(GaladrilInferenceError, KeyError):
    """Raised when a requested model is not in the registry."""


class ModelNotReadyError(GaladrilInferenceError, RuntimeError):
    """Raised when predict() is called on a model that hasn't been loaded."""


class ModelLoadError(GaladrilInferenceError):
    """Raised when a model fails to load its artifacts."""

    def __init__(self, model_name: str, reason: str) -> None:
        self.model_name = model_name
        self.reason = reason
        super().__init__(f"Failed to load model '{model_name}': {reason}")


class SchemaValidationError(GaladrilInferenceError, ValueError):
    """Raised when input features or output predictions fail schema
    validation."""

    def __init__(self, model_name: str, errors: list[str]) -> None:
        self.model_name = model_name
        self.errors = errors
        super().__init__(
            f"Schema validation failed for model '{model_name}': "
            + "; ".join(errors)
        )


class ArtifactResolutionError(GaladrilInferenceError, FileNotFoundError):
    """Raised when an artifact cannot be found or resolved."""

    def __init__(self, model_name: str, version: str, backend: str) -> None:
        self.model_name = model_name
        self.version = version
        super().__init__(
            f"Cannot resolve artifact for '{model_name}' v{version} "
            f"from backend '{backend}'."
        )
