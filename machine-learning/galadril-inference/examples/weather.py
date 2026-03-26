"""Example: TimesFM weather prevision on Paris."""

import json
import urllib.request
from pathlib import Path

from galadril_inference import InferenceEngine, PredictionRequest
from galadril_inference.storage.local import LocalLoader

EXAMPLES_DIR = Path(__file__).parent.resolve()
ARTIFACTS_DIR = EXAMPLES_DIR / "artifacts"
MODEL_ARTIFACT_PATH = ARTIFACTS_DIR / "timesfm_forecast" / "1.0.0"


def ensure_artifact_dir() -> None:
    """Create directory structure for LocalLoader."""
    if not MODEL_ARTIFACT_PATH.exists():
        MODEL_ARTIFACT_PATH.mkdir(parents=True, exist_ok=True)
        (MODEL_ARTIFACT_PATH / ".ready").touch()


def fetch_weather_data(
    lat: float, lon: float, past_days: int = 8
) -> tuple[list[float], list[str]]:
    """Fetch history including today's actual data for comparison."""
    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}&"
        f"past_days={past_days}&forecast_days=0&"
        f"hourly=temperature_2m"
    )
    print(
        f"Fetching weather data (History + Today) for Lat: {lat}, Lon: {lon}..."
    )

    req = urllib.request.Request(
        url, headers={"User-Agent": "Galadril-Inference/1.0"}
    )
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode("utf-8"))

    temps = data.get("hourly", {}).get("temperature_2m", [])
    times = data.get("hourly", {}).get("time", [])

    return temps, times


def main() -> None:
    ensure_artifact_dir()

    # Paris coordinates.
    LATITUDE, LONGITUDE = 48.8566, 2.3522

    all_temps, all_times = fetch_weather_data(LATITUDE, LONGITUDE, past_days=8)

    actual_today = all_temps[-24:]
    history_until_yesterday = all_temps[:-24]
    today_timestamps = all_times[-24:]

    engine = InferenceEngine(loader=LocalLoader(ARTIFACTS_DIR))
    engine.load_model("timesfm_forecast")

    print(
        f"Forecasting today's temperatures based on previous {len(history_until_yesterday)} hours..."
    )
    result = engine.predict(
        PredictionRequest(
            model_name="timesfm_forecast",
            features={
                "history": [
                    t for t in history_until_yesterday if t is not None
                ],
                "horizon": 24,
            },
        )
    )

    scenarios = result.prediction["scenarios"]

    print(f"\nComparison: Today's Forecast vs Actual (Paris)")
    print(
        f"{'Time':<20} | {'Actual':<8} | {'P10 (Low)':<10} | {'P50 (Likely)':<12} | {'P90 (High)':<10}"
    )
    print("-" * 70)

    for i in range(0, 24, 3):
        time_str = today_timestamps[i].replace("T", " ")
        actual = (
            f"{actual_today[i]:.1f}°C" if actual_today[i] is not None else "N/A"
        )
        p10 = f"{scenarios['low_scenario'][i]:.1f}°C"
        p50 = f"{scenarios['most_likely'][i]:.1f}°C"
        p90 = f"{scenarios['high_scenario'][i]:.1f}°C"

        print(
            f"{time_str:<20} | {actual:<8} | {p10:<10} | {p50:<12} | {p90:<10}"
        )

    print(f"Latency: {result.latency_ms:.1f}ms")


if __name__ == "__main__":
    main()
