"""Pure Python logical validator for Layer 3."""

import logging
from typing import Any, Callable

from eru.exceptions import LogicValidationError
from eru.types import TGraph

logger = logging.getLogger(__name__)


class EskgLogicValidator:
    """
    Enforces ESKG mathematical axioms on the extracted graph using pure Python.
    This avoids Numba/PyReason compatibility issues with Python 3.13+.
    """

    def __init__(
        self,
        get_entities: Callable[[TGraph], list[Any]],
        get_relations: Callable[[TGraph], list[Any]],
        entity_type_attr: str = "type",
        relation_type_attr: str = "relation_type",
        source_attr: str = "source_id",
        target_attr: str = "target_id",
    ) -> None:
        """Initialize the validator with mappings to the user's Pydantic schema."""
        self.get_entities = get_entities
        self.get_relations = get_relations
        self.entity_type_attr = entity_type_attr
        self.relation_type_attr = relation_type_attr
        self.source_attr = source_attr
        self.target_attr = target_attr

    def validate(self, graph: TGraph) -> TGraph:
        """Run logical validation and prune mathematically impossible relations."""
        try:
            entity_types = {
                getattr(ent, "id"): getattr(ent, self.entity_type_attr)
                for ent in self.get_entities(graph)
            }

            valid_relations = []
            invalid_count = 0

            for rel in self.get_relations(graph):
                source_id = getattr(rel, self.source_attr)
                target_id = getattr(rel, self.target_attr)
                rel_type = getattr(rel, self.relation_type_attr)

                base_rel = (
                    rel_type.split("_")[0]
                    if isinstance(rel_type, str)
                    else rel_type
                )

                source_type = entity_types.get(source_id)
                target_type = entity_types.get(target_id)

                if not source_type or not target_type:
                    logger.warning(
                        f"Relation {base_rel} dropped: missing source or target entity."
                    )
                    invalid_count += 1
                    continue

                is_valid = True

                # Axiom 1: Triggers (Event -> State).
                if base_rel == "triggers":
                    if source_type != "EVENT" or target_type != "STATE":
                        is_valid = False

                # Axiom 2: Leads to (Event -> Event).
                elif base_rel == "leads":
                    if source_type != "EVENT" or target_type != "EVENT":
                        is_valid = False

                # Axiom 3: Evolution (State -> State).
                elif base_rel == "evolution":
                    if source_type != "STATE" or target_type != "STATE":
                        is_valid = False

                if is_valid:
                    valid_relations.append(rel)
                else:
                    logger.debug(
                        f"Pruned invalid relation: {source_type} ({source_id}) "
                        f"-[{base_rel}]-> {target_type} ({target_id})"
                    )
                    invalid_count += 1

            if invalid_count > 0:
                logger.warning(
                    f"Pruned {invalid_count} invalid ESKG relations."
                )
                return self._rebuild_graph(graph, valid_relations)

            return graph

        except Exception as e:
            raise LogicValidationError(
                f"ESKG logic validation failed: {e}"
            ) from e

    def _rebuild_graph(
        self, graph: TGraph, valid_relations: list[Any]
    ) -> TGraph:
        """Return a new Pydantic instance with invalid relations removed."""
        graph_dict = graph.model_dump()

        for field_name, field_val in graph_dict.items():
            if isinstance(field_val, list) and len(field_val) == len(
                self.get_relations(graph)
            ):
                graph_dict[field_name] = [
                    r.model_dump() for r in valid_relations
                ]
                break

        return type(graph).model_validate(graph_dict)
