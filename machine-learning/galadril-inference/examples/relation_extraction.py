"""Compare two extraction models: Gliner2 and NuExtract2."""

from galadril_inference.core.engine import InferenceEngine
from galadril_inference.common.types import PredictionRequest
from galadril_inference.loading.loader import ArtifactLoader

TEXT = (
    "Le 12 Mars, la frappe aérienne a détruit le pont principal de Kiev, "
    "provoquant l'effondrement de la logistique de l'armée adverse de 40%."
)

ESKG_DEFINITIONS = """
You are an expert intelligence analyst extracting an Event-State Knowledge Graph (ESKG).
Use the following definitions to classify the entities and relations:

ENTITIES:
- Event: A discrete occurrence happening at a specific time (e.g., an attack, a meeting, a transaction).
- State: A stable condition resulting from an event (e.g., destroyed bridge, bankrupt company).
- Property: A numerical or qualitative metric (e.g., 40%, 100 million dollars).
- Concept: An abstract idea, strategy, or doctrine.

RELATIONS:
- TRIGGERS: An Event directly causes a new State (Event -> State).
- LEADS_TO: An Event logically or temporally precedes another Event (Event -> Event).
- EVOLVES_TO: A natural progression from one State to another State (State -> State).
- INFLUENCES: An Event modifies a Property (Event -> Property).
- OCCURS_AT: Anchors an Event to a Location or Time (Event -> Location/Time).
- INVOLVES: Links a Person/Organization/Vehicle to an Event or State.
"""

ESKG_TEMPLATE = {
    "entities": [
        {
            "name": "string",
            "type": [
                "Event",
                "State",
                "Property",
                "Location",
                "Time",
                "Person",
                "Organization",
            ],
        }
    ],
    "relations": [
        {
            "source": "string",
            "relation_type": [
                "TRIGGERS",
                "LEADS_TO",
                "EVOLVES_TO",
                "OCCURS_AT",
                "INFLUENCES",
                "INVOLVES",
            ],
            "target": "string",
        }
    ],
}


class UnifiedLoader(ArtifactLoader):
    def resolve(self, name: str, version: str) -> str:
        mapping = {
            "nuextract": "numind/NuExtract-2.0-2B",
            "gliner2": "fastino/gliner2-multi-v1",
        }
        return mapping.get(name)

    def exists(self, name: str, version: str) -> bool:
        return name in ["nuextract", "gliner2"]


def print_results(model_name, prediction, latency):
    print(f"\n{'=' * 20} RESULTS: {model_name.upper()} {'=' * 20}")
    print(f"Latency: {latency:.2f} ms")

    print("\n[ENTITIES]")
    entities = prediction.get("entities", [])
    if isinstance(entities, dict):
        for etype, values in entities.items():
            print(f"  - {etype}: {', '.join(values) if values else 'None'}")
    else:
        for ent in entities:
            print(f"  - {ent.get('type')}: {ent.get('name')}")

    print("\n[RELATIONS]")
    relations = prediction.get("relations", [])
    if not relations:
        print("  No relations detected.")
    for rel in relations:
        print(
            f"  ({rel.get('source')}) --[{rel.get('relation_type')}]--> ({rel.get('target')})"
        )


def main():
    loader = UnifiedLoader()
    engine = InferenceEngine(loader=loader)

    models_to_test = ["gliner2", "nuextract"]

    for model_id in models_to_test:
        engine.load_model(model_id)

        if model_id == "nuextract":
            features = {
                "text": f"{ESKG_DEFINITIONS}\nText: {TEXT}",
                "template": ESKG_TEMPLATE,
            }
        else:
            features = {"text": TEXT}

        req = PredictionRequest(model_name=model_id, features=features)

        try:
            result = engine.predict(req)
            print_results(model_id, result.prediction, result.latency_ms)
        except Exception as e:
            print(f"Error with {model_id}: {e}")

        engine.unload_model(model_id)


if __name__ == "__main__":
    main()
