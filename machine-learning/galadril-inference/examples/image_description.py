"""Example script demonstrating multimodal vector search with SigLIP."""

import numpy as np
import cv2
from PIL import Image
from pathlib import Path

from galadril_inference.core.engine import InferenceEngine
from galadril_inference.common.types import PredictionRequest
from galadril_inference.loading.loader import ArtifactLoader

EXAMPLES_DIR = Path(__file__).parent.resolve()
IMAGES = {
    "Satellite": EXAMPLES_DIR / "images" / "military_satellite.png",
    "Gazelle": EXAMPLES_DIR / "images" / "gazelle.png",
}

CANDIDATES = {
    "Satellite": [
        "Aerial view of a large industrial or construction site featuring a grid-like network of dirt roads, excavated ground, and several rectangular storage containers scattered across the field",
        # this is the truth.
        "Satellite imagery showing a massive military staging area with hundreds of armored vehicles and trucks organized in neat rows on a muddy terrain with visible track marks.",
        "A close-up photograph of a microscopic circuit board showing complex copper wiring, transistors, and silver soldering points on a dark silicon substrate",
        "Satellite imagery detailing a strategic military compound. Clearly visible are four T-72 main battle tanks parked at the front gate, a central helicopter landing pad with a stationary Mi-24 Hind gunship, and dozens of personnel moving between the vehicles under camouflage netting. The fresh snowfall shows multiple footprints leading to the command tents.",
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
