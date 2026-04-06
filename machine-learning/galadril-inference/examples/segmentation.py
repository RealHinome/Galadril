"""Promptable segmentation with Grounded SAM."""

from pathlib import Path

import cv2
import numpy as np

from galadril_inference import InferenceEngine, PredictionRequest
from galadril_inference.loading.loader import ArtifactLoader


class HuggingFaceMockLoader(ArtifactLoader):
    def resolve(self, name: str, version: str) -> str:
        return "grounded_sam_models"

    def exists(self, name: str, version: str) -> bool:
        return name == "grounded_sam"


EXAMPLES_DIR = Path(__file__).parent.resolve()
IMAGE_PATH = EXAMPLES_DIR / "images" / "military_camp.png"
OUTPUT_PATH = EXAMPLES_DIR / "images" / "military_camp_detected.png"

COLORS = {
    "soldier": (0, 255, 0),
    "tent": (0, 0, 255),
    "satellite dish": (255, 0, 0),
    "default": (255, 255, 0),
}


def main() -> None:
    """Run Grounded SAM inference."""
    IMAGE_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not IMAGE_PATH.exists():
        print(f"Please place an image file at {IMAGE_PATH} before running.")
        return

    loader = HuggingFaceMockLoader()
    engine = InferenceEngine(loader=loader)

    engine.load_model("grounded_sam")

    image_bgr = cv2.imread(str(IMAGE_PATH))
    image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)

    concepts_to_find = "soldier. tent. satellite dish"
    print(f"\nSegmenting {concepts_to_find}...")

    request = PredictionRequest(
        model_name="grounded_sam",
        features={
            "image": image_rgb,
            "text": concepts_to_find,
            "threshold": 0.3,
            "use_tiling": True,
            "tile_size": 640,
            "tile_overlap": 0.25,
            "nms_threshold": 0.25,
            "return_masks": False,
        },
    )
    result = engine.predict(request)

    concepts = result.prediction["concepts"]
    canvas = image_bgr.copy()

    print(
        f"\nTotal objects found: {result.prediction['total_objects']} (Latency: {result.latency_ms:.1f}ms):"
    )

    for name, data in concepts.items():
        color = COLORS.get(name.lower(), COLORS["default"])
        print(f"\n  {name}: {data['count']} found")

        for i, inst in enumerate(data["instances"]):
            box = inst["box"]
            x1, y1, x2, y2 = map(int, box)
            cv2.rectangle(canvas, (x1, y1), (x2, y2), color, 2)

            if inst.get("mask"):
                mask_np = np.array(inst["mask"], dtype=np.uint8)
                contours, _ = cv2.findContours(
                    mask_np, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
                )
                cv2.drawContours(canvas, contours, -1, color, 2)

            label = f"{name} {inst['score']:.2f}"
            (w, h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            cv2.rectangle(canvas, (x1, y1 - h - 5), (x1 + w, y1), color, -1)
            cv2.putText(
                canvas,
                label,
                (x1, y1 - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 255),
                1,
            )

    cv2.imwrite(str(OUTPUT_PATH), canvas)
    print(f"\nImage saved to: {OUTPUT_PATH}")

    engine.unload_model("grounded_sam")


if __name__ == "__main__":
    main()
