"""Vector comparaison using BGE-M3 for weapons."""

from pathlib import Path

import time
import numpy as np

from galadril_inference.core.engine import InferenceEngine
from galadril_inference.common.types import PredictionRequest
from galadril_inference.loading.loader import ArtifactLoader

CANDIDATES = [
    "TLAM salvos",
    "Tomahawk",
    "BGM-109",
    "M51",
    "K-550 Alexander Nevsky",
    "Project 941 Akula",
]

QUERIES = [
    "Tomahawk Land Attack Missile",
    "M51 strategic ballistic missile",
    "A long-range missile system",
    "A nuclear-powered submarine",
    "A naval vessel with alphanumeric designation",
]


class LocalMockLoader(ArtifactLoader):
    def resolve(self, name: str, version: str) -> str:
        return str(Path(__file__).parent.resolve() / "artifacts" / "bge_m3")

    def exists(self, name: str, version: str) -> bool:
        return name == "bge_m3"


def get_dense_embedding(engine, text):
    feat = {"text": text}
    req = PredictionRequest(model_name="bge_m3", features=feat)

    start_time = time.perf_counter()
    prediction = engine.predict(req).prediction["dense"]
    end_time = time.perf_counter()

    duration_ms = (end_time - start_time) * 1000
    return np.array(prediction), duration_ms


def main():
    loader = LocalMockLoader()
    engine = InferenceEngine(loader=loader)
    engine.load_model("bge_m3")

    candidate_vecs = {}
    for txt in CANDIDATES:
        vec, duration = get_dense_embedding(engine, txt)
        candidate_vecs[txt] = vec
        if txt == CANDIDATES[0]:
            print(f"Embedding size: {vec.shape[0]}")
            print(f"Mean time: {duration:.2f} ms")

    for query in QUERIES:
        query_vec, q_duration = get_dense_embedding(engine, query)
        print(f"\nQuery: '{query}' ({q_duration:.2f} ms)")

        results = []
        for name, vec in candidate_vecs.items():
            score = np.dot(query_vec, vec)
            results.append((score, name))

        for score, name in sorted(results, reverse=True):
            print(f"    Score: {score:.4f} | Candidate: {name}")

    engine.unload_model("bge_m3")


if __name__ == "__main__":
    main()
