"""Compare two extraction models: Gliner2."""

from galadril_inference.core.engine import InferenceEngine
from galadril_inference.common.types import PredictionRequest
from galadril_inference.loading.loader import ArtifactLoader

TEXT = (
    "On March 12, the airstrike destroyed the main bridge in Kyiv, "
    "causing the enemy army's logistics to collapse by 40%."
)


class UnifiedLoader(ArtifactLoader):
    def resolve(self, name: str, version: str) -> str:
        mapping = {
            "gliner2": "fastino/gliner2-large-v1",
        }
        return mapping.get(name)

    def exists(self, name: str, version: str) -> bool:
        return name in ["gliner2"]


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
