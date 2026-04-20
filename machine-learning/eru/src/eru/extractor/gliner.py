"""GLiNER-based candidate extractor for Layer 1."""

import logging

from gliner import GLiNER

from eru.exceptions import ExtractionError
from eru.types import ExtractedCandidate

logger = logging.getLogger(__name__)


class GlinerExtractor:
    """Extracts entities using the GLiNER bi-encoder architecture."""

    def __init__(
        self,
        labels: list[str],
        model_id: str = "knowledgator/gliner-bi-base-v2.0",
        threshold: float = 0.3,
        device: str = "cpu",
    ) -> None:
        self.labels = labels
        self.threshold = threshold

        try:
            self.model = GLiNER.from_pretrained(model_id).to(device)
            self.label_embeddings = self.model.encode_labels(self.labels)
        except Exception as e:
            raise ExtractionError(f"Failed to load GLiNER model: {e}") from e

    def extract(self, text: str) -> list[ExtractedCandidate]:
        """Extract entity spans and remove exact duplicates."""
        if not text.strip():
            return []

        try:
            raw_outputs = self.model.batch_predict_with_embeds(
                [text], self.label_embeddings, self.labels
            )[0]

            unique_candidates = []
            seen_entities = set()

            for ent in raw_outputs:
                if ent.get("score", 1.0) < self.threshold:
                    continue

                text_clean = ent["text"].strip()
                unique_key = (text_clean.lower(), ent["label"])

                if unique_key not in seen_entities:
                    seen_entities.add(unique_key)
                    unique_candidates.append(
                        ExtractedCandidate(
                            text=text_clean,
                            label=ent["label"],
                            start_char=ent["start"],
                            end_char=ent["end"],
                            metadata={"score": float(ent.get("score", 0.0))},
                        )
                    )

            return unique_candidates

        except Exception as e:
            raise ExtractionError(f"GLiNER extraction failed: {e}") from e
