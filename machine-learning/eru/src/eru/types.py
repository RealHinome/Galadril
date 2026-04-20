"""Core types and interfaces for the Eru engine."""

from __future__ import annotations

from typing import Any, Protocol, TypeVar
from pydantic import BaseModel

# TGraph represents the user-defined Pydantic schema for their specific domain.
TGraph = TypeVar("TGraph", bound=BaseModel)


class ExtractedCandidate(BaseModel):
    """
    Standardized representation of an entity candidate extracted in Layer 1.
    This prevents the LLM from hallucinating spans.
    """

    text: str
    label: str
    start_char: int
    end_char: int
    metadata: dict[str, Any] = {}


class CandidateExtractor(Protocol):
    """Protocol for Layer 1: The entity span extractor."""

    def extract(self, text: str) -> list[ExtractedCandidate]:
        """
        Extract candidate entities from raw text.
        """
        ...


class SemanticReasoner(Protocol):
    """Protocol for Layer 2: The constrained LLM reasoner."""

    def reason(
        self,
        text: str,
        candidates: list[ExtractedCandidate],
        schema: type[TGraph],
    ) -> TGraph:
        """
        Relate extracted candidates using a strictly constrained LLM.
        """
        ...


class RelationDef(BaseModel):
    """Structured definition of a relation to guide the LLM reasoning."""

    name: str
    description: str
    examples: list[str] = []


class LogicValidator(Protocol):
    """Protocol for Layer 3: The logical rule engine."""

    def validate(self, graph: TGraph) -> TGraph:
        """
        Validate the generated graph against deterministic logical rules.
        Invalid relations should be pruned or flagged.
        """
        ...
