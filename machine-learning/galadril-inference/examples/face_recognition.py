"""Example: Face recognition with automatic model download."""

from pathlib import Path

import cv2
from galadril_inference import InferenceEngine, PredictionRequest
from galadril_inference.storage.local import LocalLoader
from insightface.app import FaceAnalysis

EXAMPLES_DIR = Path(__file__).parent.resolve()
ARTIFACTS_DIR = EXAMPLES_DIR / "artifacts"
MODEL_DIR = ARTIFACTS_DIR / "face_recognition" / "1.0.0"
IMAGE_PATH = EXAMPLES_DIR / "image.jpg"


def ensure_model_downloaded() -> None:
    """Download the InsightFace model pack if not already present."""
    marker = MODEL_DIR / "models" / "buffalo_sc"
    if marker.exists() and any(marker.iterdir()):
        print("Model already downloaded, skipping.")
        return

    print("Downloading InsightFace buffalo_sc model...")
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    app = FaceAnalysis(
        name="buffalo_sc",
        root=str(MODEL_DIR),
        allowed_modules=["detection", "recognition"],
        providers=["CPUExecutionProvider"],
    )
    app.prepare(ctx_id=-1, det_size=(640, 640))
    print("Model downloaded.")


def main() -> None:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

    ensure_model_downloaded()

    engine = InferenceEngine(loader=LocalLoader(ARTIFACTS_DIR))
    engine.load_model("face_recognition")

    image = cv2.imread(str(IMAGE_PATH))
    if image is None:
        print(
            f"Error: could not read image at {IMAGE_PATH}. Check if the file exists."
        )
        return

    result = engine.predict(
        PredictionRequest(
            model_name="face_recognition",
            features={"action": "embed", "image": image},
        )
    )

    faces = result.prediction["faces"]
    print(
        f"\nFound {len(faces)} face(s)  (latency: {result.latency_ms:.1f}ms)\n"
    )

    for i, face in enumerate(faces):
        emb = face.get("embedding")
        print(
            f"  Face {i}: confidence={face['confidence']:.3f}  "
            f"embedding_dim={len(emb) if emb else 0}"
        )


if __name__ == "__main__":
    main()
