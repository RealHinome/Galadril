"""The core orchestrator for the ESKG extraction pipeline."""

import logging
from typing import Generic

from pydantic import BaseModel, ValidationError

from eru.exceptions import ExtractionError, LogicValidationError, ReasoningError
from eru.types import (
    CandidateExtractor,
    LogicValidator,
    SemanticReasoner,
    TGraph,
)

logger = logging.getLogger(__name__)


class EskgEngine(Generic[TGraph]):
    """
    The main Event-State Knowledge Graph extraction engine.

    This engine coordinates the three layers of the Eru pipeline:
    1. Candidate Extraction (NER)
    2. Semantic Reasoning (Constrained LLM)
    3. Logical Validation (PyReason)
    """

    def __init__(
        self,
        schema: type[TGraph],
        extractor: CandidateExtractor,
        reasoner: SemanticReasoner,
        validator: LogicValidator | None = None,
    ) -> None:
        """
        Initialize the ESKG Engine.
        """
        self.schema = schema
        self.extractor = extractor
        self.reasoner = reasoner
        self.validator = validator

        logger.info(f"Initialized EskgEngine with schema: {schema.__name__}")

    def process(self, text: str) -> TGraph:
        """
        Execute the full extraction pipeline on the given text.
        """
        if not text or not text.strip():
            raise ValueError("Input text cannot be empty or whitespace.")

        try:
            logger.debug("Starting Layer 1: Candidate Extraction")
            candidates = self.extractor.extract(text)
            logger.debug(f"Extracted {len(candidates)} candidates.")
        except Exception as e:
            logger.error(f"Layer 1 extraction failed: {e}")
            raise ExtractionError(f"Failed to extract candidates: {e}") from e

        try:
            logger.debug("Starting Layer 2: Semantic Reasoning (LLM)")
            graph = self.reasoner.reason(text, candidates, self.schema)
        except ValidationError as e:
            logger.error(f"Layer 2 generated invalid schema: {e}")
            raise ReasoningError(
                "LLM output did not match the required schema."
            ) from e
        except Exception as e:
            logger.error(f"Layer 2 reasoning failed: {e}")
            raise ReasoningError(f"Semantic reasoning failed: {e}") from e

        if self.validator:
            try:
                logger.debug("Starting Layer 3: Logical Validation")
                graph = self.validator.validate(graph)
            except Exception as e:
                logger.error(f"Layer 3 logical validation failed: {e}")
                raise LogicValidationError(f"Validation failed: {e}") from e
        else:
            logger.debug("No LogicValidator provided. Skipping Layer 3.")

        logger.info("ESKG pipeline completed successfully.")
        return graph
