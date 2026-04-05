"""Example script demonstrating multimodal vector search with SigLIP."""

import numpy as np
import cv2
from pathlib import Path

from galadril_inference.core.engine import InferenceEngine
from galadril_inference.common.types import PredictionRequest
from galadril_inference.loading.loader import ArtifactLoader

EXAMPLES_DIR = Path(__file__).parent.resolve()
IMAGES = {
    "Satellite": EXAMPLES_DIR / "images" / "military_camp.png",
    "Gazelle": EXAMPLES_DIR / "images" / "gazelle.png",
}

CANDIDATES = {
    "Satellite": [
        # this is the truth.
        "A high-angle wide shot of a military tactical operations center established in a grassy field. Large olive-drab modular tents are connected in a complex layout, secured by a perimeter of concertina wire and chain-link fencing. Several personnel in camouflage uniforms are visible near a portable light tower and a satellite dish, while a large tan building and a communications mast sit in the background under an overcast sky.",
        "An aerial view of a large-scale disaster relief base camp set up following a hurricane. Rows of dark green emergency medical shelters and supply depots are arranged on a damp lawn. Aid workers in high-visibility vests move between the temporary structures and portable generators, while a Red Cross logistics center and a radio tower stand in the distance against a gloomy, gray horizon.",
        "A wide-angle view of an expansive military encampment featuring dozens of bright orange and white inflatable hangars linked together on a field. Soldiers in combat gear are patrolling the perimeter fence, which is reinforced with barbed wire. In the background, a massive industrial warehouse and a cell tower are visible under a thick layer of storm clouds.",
    ],
    "Gazelle": [
        "Sud-Aviation SA342 Gazelle",  # this is the truth.
        "Eurocopter EC665 Tiger",
        "Sud-Aviation SA316 Alouette III",
        "NHIndustries NH90",
    ],
}


class HuggingFaceMockLoader(ArtifactLoader):
    def resolve(self, name: str, version: str) -> str:
        return "google/siglip2-so400m-patch16-naflex"

    def exists(self, name: str, version: str) -> bool:
        return name == "siglip2"


def get_embedding(engine, action, data):
    feat = {"action": f"embed_{action}", action: data}
    req = PredictionRequest(model_name="siglip2", features=feat)
    return np.array(engine.predict(req).prediction["embedding"])


def main():
    loader = HuggingFaceMockLoader()
    engine = InferenceEngine(loader=loader)
    engine.load_model("siglip2")

    for name, path in IMAGES.items():
        img_array = np.array(cv2.imread(str(path)))
        img_vec = get_embedding(engine, "image", img_array)
        print(f"Shape: {img_vec.shape}")

        results = []
        for text in CANDIDATES[name]:
            txt_vec = get_embedding(engine, "text", text)
            score = np.dot(img_vec, txt_vec)
            results.append((score, text))

        for score, text in sorted(results, reverse=True):
            print(f"    Score: {score:.4f} | Text: '{text[:70]}...'")

    engine.unload_model("siglip2")


if __name__ == "__main__":
    main()
