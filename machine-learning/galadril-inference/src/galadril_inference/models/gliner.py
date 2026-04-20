"""GLiNER2 model for joint entity and relation extraction."""

from __future__ import annotations

from typing import Any

import structlog

from galadril_inference.common.exceptions import (
    ModelLoadError,
    SchemaValidationError,
)
from galadril_inference.common.types import (
    ModelMeta,
    PredictionRequest,
    PredictionResult,
)
from galadril_inference.models.base import BaseModel

logger = structlog.get_logger(__name__)

_MODEL_NAME = "gliner2"
_MODEL_VERSION = "1.0.0"


class GlinerModel(BaseModel):
    """GLiNER2 for zero-shot entity and relation extraction."""

    def __init__(self) -> None:
        self._model = None

    def meta(self) -> ModelMeta:
        return ModelMeta(
            name=_MODEL_NAME,
            version=_MODEL_VERSION,
            description="GLiNER2 model for joint entity and relation extraction.",
            tags={
                "domain": "nlp",
                "task": "information_extraction",
                "framework": "pytorch",
            },
        )

    def load(self, artifact_path: str = "fastino/gliner2-large-v1") -> None:
        try:
            from gliner2 import GLiNER2
        except ImportError as exc:
            raise ModelLoadError(
                _MODEL_NAME,
                "Missing dependency 'gliner2'. Please install it.",
            ) from exc

        try:
            self._model = GLiNER2.from_pretrained(
                artifact_path, quantize=True, compile=True
            )
            logger.info(
                "model_loaded", model_name=_MODEL_NAME, path=artifact_path
            )
        except Exception as exc:
            raise ModelLoadError(_MODEL_NAME, str(exc)) from exc

    def cleanup(self) -> None:
        self._model = None
        import torch

        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    def predict(self, request: PredictionRequest) -> PredictionResult:
        self._ensure_loaded()

        text = request.features.get("text")
        if not text or not isinstance(text, str):
            raise SchemaValidationError(
                _MODEL_NAME, ["Missing or invalid 'text' prompt."]
            )

        default_entities = {
            "event": "Action, incident, or discrete occurrence. Must be an active verb-based concept (e.g., 'Attack', 'Movement'). Cannot be a static object.",
            "condition_status": "Condition, status, or qualitative result. Must describe 'how' something is after.",
            "metric_value": "Numerical value, percentage metric, or specific attribute. Must be quantifiable.",
            "location": "Geographical place, facility, or spatial point. Specific names or coordinates. If it's a building being hit, it's a Target; if it's the city around it, it's a Location.",
            "time": "Specific date, time, or period.",
            "person": "Individual human being. Named individuals or specific ranks/roles.",
            "actor_entity": "Group, army, company, or institution. Collective entities acting as agents.",
            "weapon": "Military equipment or armament used.",
            "target": "Physical object or system receiving the action. Can be infrastructure or abstract systems.",
        }

        default_relations = {
            "initiates_status": "Causal relationship where an event initiates a new state",
            "results_in_event": "Sequential relationship where one event causes another",
            "progresses_to": "Progression relationship where one state leads to another",
            "modifies_metric": "Impact relationship where an entity modifies a property",
            "located_at": "Spatio-temporal anchoring of an event",
            "utilizes_weapon": "Instrumental relationship: Specifies the armament, equipment, or tool used to carry out the event.",
            "targets_object": "Objective relationship: Identifies the physical infrastructure, system, or entity that is the intended victim of the event.",
            "executed_by": "Agentic relationship: Links the event to the specific actor entity, group, or person responsible for carrying it out.",
            "is_part_of": "Hierarchical inclusion of an entity within another",
        }

        entity_types = request.features.get("entities", default_entities)
        relation_types = request.features.get("relations", default_relations)

        try:
            schema = (
                self._model.create_schema()
                .entities(entity_types)
                .relations(relation_types)
            )

            results = self._model.extract(text, schema)

            raw_entities = results.get("entities", {})
            raw_relations = results.get("relation_extraction", {})

            structured_relations = []
            for rel_type, rel_list in raw_relations.items():
                for head, tail in rel_list:
                    structured_relations.append(
                        {
                            "source": head,
                            "target": tail,
                            "relation_type": rel_type,
                        }
                    )

            return PredictionResult(
                model_name=_MODEL_NAME,
                model_version=_MODEL_VERSION,
                prediction={
                    "entities": raw_entities,
                    "relations": structured_relations,
                },
                confidence=1.0,
            )

        except Exception as exc:
            raise RuntimeError(f"GLiNER2 inference failed: {exc}") from exc

    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "required": ["text"],
            "properties": {
                "text": {"type": "string"},
                "entities": {"type": "array", "items": {"type": "string"}},
                "relations": {
                    "type": ["array", "object"],
                    "description": "List of strings or dict mapping relation name to description.",
                },
            },
        }

    def output_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "entities": {
                    "type": "object",
                    "additionalProperties": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                },
                "relations": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "source": {"type": "string"},
                            "target": {"type": "string"},
                            "relation_type": {"type": "string"},
                        },
                    },
                },
            },
        }

    def _ensure_loaded(self) -> None:
        if self._model is None:
            raise ModelLoadError(_MODEL_NAME, "Model is not loaded.")
