"""Custom exceptions for the Eru ESKG pipeline."""


class EruError(Exception):
    """Base exception for all Eru-related errors."""

    pass


class ExtractionError(EruError):
    """Raised when the candidate extractor fails."""

    pass


class ReasoningError(EruError):
    """Raised when the semantic reasoner fails to generate a valid graph."""

    pass


class LogicValidationError(EruError):
    """Raised when the logic validator encounters an unrecoverable error."""

    pass
