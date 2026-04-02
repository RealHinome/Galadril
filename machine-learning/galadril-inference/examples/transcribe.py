"""Speech recognition with optional Diarization."""

import os
from pathlib import Path

from galadril_inference import InferenceEngine, PredictionRequest
from galadril_inference.loading.loader import ArtifactLoader


class HuggingFaceMockLoader(ArtifactLoader):
    def resolve(self, name: str, version: str) -> str:
        return "openai/whisper-large-v3"

    def exists(self, name: str, version: str) -> bool:
        return name == "whisper"


EXAMPLES_DIR = Path(__file__).parent.resolve()
AUDIO_PATH = EXAMPLES_DIR / "audio" / "galadriel.mp3"


def main() -> None:
    """Run the Whisper inference example with dynamic diarization support."""
    AUDIO_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not AUDIO_PATH.exists():
        print(f"No file found at {AUDIO_PATH}.")
        return

    hf_token_available = bool(os.environ.get("HF_TOKEN"))

    if hf_token_available:
        print("HF_TOKEN detected: Diarization will be ENABLED.")
    else:
        print("No HF_TOKEN detected: Running in TRANSCRIPTION-ONLY mode.")

    loader = HuggingFaceMockLoader()
    engine = InferenceEngine(loader=loader)

    engine.load_model("whisper")

    request = PredictionRequest(
        model_name="whisper",
        features={
            "audio": str(AUDIO_PATH),
            "task": "transcribe",
            "enable_diarization": hf_token_available,
        },
    )

    result = engine.predict(request)
    prediction = result.prediction

    current_speaker = None
    for chunk in prediction["chunks"]:
        ts = chunk["timestamp"]
        end_time = f"{ts[1]:.2f}" if ts[1] else "end"
        text = chunk["text"].strip()

        if hf_token_available and "speaker" in chunk:
            speaker = chunk.get("speaker", "UNKNOWN")
            if speaker != current_speaker:
                print(f"\n[{speaker}]:")
                current_speaker = speaker
            print(f"  ({ts[0]:.2f}s - {end_time}s) {text}")
        else:
            print(f"[{ts[0]:.2f}s - {end_time}s] {text}")

    print(f"\nLatency: {result.latency_ms:.2f} ms")

    engine.unload_model("whisper")


if __name__ == "__main__":
    main()
