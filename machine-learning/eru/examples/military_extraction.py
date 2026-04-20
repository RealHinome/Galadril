"""Demonstrate the Eru pipeline on a short military text."""

import json
from typing import Literal, get_args
from transformers import AutoModelForCausalLM, AutoTokenizer

import outlines
from pydantic import BaseModel, Field

from eru.engine import EskgEngine
from eru.extractor.gliner import GlinerExtractor
from eru.logic.simple import EskgLogicValidator
from eru.reasoner.outlines import OutlinesReasoner
from eru.types import RelationDef

labels = Literal[
    "WEAPON",
    "FACILITY",
    "DATE",
    "PERSON",
    "ORGANIZATION",
    "INTENT",
    "VEHICLE",
    "METRIC_VALUE",
    "LOCATION",
    "EVENT",
]


class MilitaryEntity(BaseModel):
    """An extracted entity from the military domain."""

    id: str = Field(description="Unique identifier for the entity.")
    text: str = Field(description="The exact text span from the prompt.")
    type: labels


class MilitaryRelation(BaseModel):
    """A relation connecting two military entities."""

    source_id: str
    target_id: str
    relation_type: Literal[
        "triggers",
        "leads_to",
        "occurs_at",
        "target",
        "authorized_by",
        "employs",
        "located_in",
        "aims_to",
        "has_duration",
        "has_intent",
    ]


class MilitaryGraph(BaseModel):
    """The full ESKG graph output."""

    entities: list[MilitaryEntity]
    relations: list[MilitaryRelation]


relation_definitions = [
    RelationDef(
        name="authorized_by",
        description="Legal or command hierarchy link between an operation and a decision-maker.",
        examples=[
            "A mission approved by a General",
            "A strike ordered by the High Command",
        ],
    ),
    RelationDef(
        name="employs",
        description="The use of a specific asset, weapon, or unit during an event.",
        examples=[
            "A task force using radar systems",
            "An infantry squad utilizing night vision",
        ],
    ),
    RelationDef(
        name="target",
        description="The specific objective, facility, or enemy force being engaged.",
        examples=[
            "Artillery hitting a bridge",
            "Sabotage directed at a fuel depot",
        ],
    ),
    RelationDef(
        name="occurs_at",
        description="Temporal or geographical anchoring of an action.",
        examples=[
            "Tactical movement at 2300 hours",
            "Clash occurring in the DMZ",
        ],
    ),
    RelationDef(
        name="aims_to",
        description="Connects an EVENT to a STRATEGIC_OBJECTIVE. It describes the intended military effect.",
        examples=[
            "Operation X aims to neutralize air defenses",
            "The strike aims to disrupt supply lines",
        ],
    ),
    RelationDef(
        name="has_duration",
        description="Links an EVENT to a DATE span or duration.",
        examples=["The drill lasted 4 hours", "Phase 1 occurs within 24 hours"],
    ),
    RelationDef(
        name="located_in",
        description="Physical containment of a facility or unit within a broader area.",
        examples=[
            "A bunker inside the mountain range",
            "A fleet stationed in the Mediterranean",
        ],
    ),
    RelationDef(
        name="commanded_by",
        description="Who or what unit organized and command this EVENT.",
        examples=[
            "NSA",
            "French President",
        ],
    ),
    RelationDef(
        name="has_intent",
        description="Links a PERSON or ORGANIZATION or ACTOR or VEHICULE or WEAPON to an implicit INTENT or purpose.",
    ),
]


def main() -> None:
    text = (
        "Operation EPIC FURY commenced at 0115Z, 28 FEB 26, under directive authority of the U.S. President, "
        "executed by CENTCOM joint task elements against high-value targets within Iranian territory. "
        "Strike packages composed of B-2 stealth bombers, F-35 multirole fighters, and naval surface combatants "
        "(CVN and DDG groups) delivered precision-guided munitions and TLAM salvos against IRGC C2 nodes, "
        "integrated air defense systems, and ballistic missile complexes. Initial operational tempo exceeded "
        "1,000 target engagements within the first 24–48 hours, scaling beyond 1,250 strikes to degrade "
        "adversary warfighting capability and deny strategic missile deployment vectors. Command oversight "
        "included senior defense leadership (e.g., SecDef-level authority), coordinating multi-domain "
        "operations (air, land, maritime, cyber) across the CENTCOM AOR, including key nodes such as "
        "Kharg Island and dispersed missile launch infrastructure."
    )

    extractor = GlinerExtractor(labels=list(get_args(labels)), threshold=0.3)

    model_name = "Qwen/Qwen3-4B-Instruct-2507"
    hf_model = AutoModelForCausalLM.from_pretrained(
        model_name, device_map="auto"
    )
    hf_tokenizer = AutoTokenizer.from_pretrained(model_name)
    llm = outlines.from_transformers(hf_model, hf_tokenizer)

    reasoner = OutlinesReasoner(
        model=llm,
        relation_defs=relation_definitions,
        open_entity_types=["INTENT"],
    )

    validator = EskgLogicValidator(
        get_entities=lambda g: g.entities,
        get_relations=lambda g: g.relations,
        entity_type_attr="type",
        relation_type_attr="relation_type",
        source_attr="source_id",
        target_attr="target_id",
    )

    engine = EskgEngine(
        schema=MilitaryGraph,
        extractor=extractor,
        reasoner=reasoner,
        validator=validator,
    )

    result_graph = engine.process(text)

    print(json.dumps(result_graph.model_dump(), indent=2))


if __name__ == "__main__":
    main()
