"""NuExtract model for template-based information extraction."""

from __future__ import annotations

import json
from typing import Any

import numpy as np
import structlog
from numpy.typing import NDArray

from galadril_inference.common.exceptions import (
    ModelLoadError,
    SchemaValidationError,
)
from galadril_inference.common.types import (
    ModelMeta,
    PredictionRequest,
    PredictionResult,
)
from galadril_inference.models.base import BaseModel

logger = structlog.get_logger(__name__)

_MODEL_NAME = "nuextract"
_MODEL_VERSION = "2.0.0"


def process_all_vision_info(messages, examples=None):
    """Process vision info from both messages and in-context examples."""
    from qwen_vl_utils import process_vision_info, fetch_image

    def extract_example_images(example_item):
        if not example_item:
            return []
        examples_to_process = (
            example_item if isinstance(example_item, list) else [example_item]
        )
        images = []
        for example in examples_to_process:
            if (
                isinstance(example.get("input"), dict)
                and example["input"].get("type") == "image"
            ):
                images.append(fetch_image(example["input"]))
        return images

    is_batch = messages and isinstance(messages[0], list)
    messages_batch = messages if is_batch else [messages]
    is_batch_examples = (
        examples
        and isinstance(examples, list)
        and (isinstance(examples[0], list) or examples[0] is None)
    )
    examples_batch = (
        examples
        if is_batch_examples
        else ([examples] if examples is not None else None)
    )

    if examples and len(examples_batch) != len(messages_batch):
        if not is_batch and len(examples_batch) == 1:
            pass
        else:
            raise ValueError(
                "Examples batch length must match messages batch length"
            )

    all_images = []
    for i, message_group in enumerate(messages_batch):
        if examples and i < len(examples_batch):
            all_images.extend(extract_example_images(examples_batch[i]))
        input_message_images = process_vision_info(message_group)[0] or []
        all_images.extend(input_message_images)

    return all_images if all_images else None


class NuExtractModel(BaseModel):
    """NuExtract model for structured extraction from text or images."""

    def __init__(self) -> None:
        self._model = None
        self._processor = None
        self._device = "cpu"

    def meta(self) -> ModelMeta:
        return ModelMeta(
            name=_MODEL_NAME,
            version=_MODEL_VERSION,
            description="NuExtract-2.0 model for structured JSON information extraction.",
            tags={
                "domain": "multimodal",
                "task": "information_extraction",
                "framework": "transformers",
            },
        )

    def load(self, artifact_path: str = "numind/NuExtract-2.0-2B") -> None:
        try:
            import torch
            from transformers import AutoProcessor, AutoModelForImageTextToText
            import qwen_vl_utils
        except ImportError as exc:
            raise ModelLoadError(
                _MODEL_NAME,
                "Missing dependencies (torch, transformers, qwen_vl_utils).",
            ) from exc

        try:
            self._device = "cuda" if torch.cuda.is_available() else "cpu"
            attn_impl = (
                "flash_attention_2" if self._device == "cuda" else "eager"
            )
            dtype = torch.bfloat16 if self._device == "cuda" else torch.float32

            self._model = AutoModelForImageTextToText.from_pretrained(
                artifact_path,
                trust_remote_code=True,
                torch_dtype=dtype,
                attn_implementation=attn_impl,
                device_map="auto" if self._device == "cuda" else None,
            )
            self._processor = AutoProcessor.from_pretrained(
                artifact_path,
                trust_remote_code=True,
                padding_side="left",
                use_fast=True,
            )
            logger.info(
                "model_loaded", model_name=_MODEL_NAME, path=artifact_path
            )
        except Exception as exc:
            raise ModelLoadError(_MODEL_NAME, str(exc)) from exc

    def cleanup(self) -> None:
        self._model = None
        self._processor = None
        import torch

        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    def predict(self, request: PredictionRequest) -> PredictionResult:
        self._ensure_loaded()
        from PIL import Image

        text = request.features.get("text", "")
        image_array = request.features.get("image")
        template = request.features.get("template")

        if not text and image_array is None:
            raise SchemaValidationError(
                _MODEL_NAME, ["Must provide either 'text' or 'image'."]
            )

        if not template:
            template = {
                "entities": [
                    {
                        "entity": "verbatim-string",
                        "type": [
                            "Event",
                            "State",
                            "Property",
                            "Location",
                            "Time",
                            "Person",
                            "Organization",
                            "Vehicle",
                            "Weapon",
                            "Concept",
                        ],
                    }
                ],
                "relations": [
                    {
                        "source": "verbatim-string",
                        "relation_type": [
                            "TRIGGERS",
                            "LEADS_TO",
                            "EVOLVES_TO",
                            "CONTAINS",
                            "OCCURS_AT",
                            "INFLUENCES",
                            "INVOLVES",
                        ],
                        "target": "verbatim-string",
                    }
                ],
            }

        template_str = (
            json.dumps(template) if isinstance(template, dict) else template
        )

        content = []
        if image_array is not None:
            pil_image = Image.fromarray(image_array).convert("RGB")
            content.append({"type": "image", "image": pil_image})
        if text:
            content.append({"type": "text", "text": text})

        messages = [
            {
                "role": "user",
                "content": content if len(content) > 1 else content[0],
            }
        ]

        try:
            formatted_text = self._processor.tokenizer.apply_chat_template(
                messages,
                template=template_str,
                tokenize=False,
                add_generation_prompt=True,
            )

            image_inputs = process_all_vision_info(messages)

            inputs = self._processor(
                text=[formatted_text],
                images=image_inputs,
                padding=True,
                return_tensors="pt",
            ).to(self._model.device)

            generation_config = {
                "do_sample": False,
                "num_beams": 1,
                "max_new_tokens": 2048,
            }

            generated_ids = self._model.generate(**inputs, **generation_config)

            generated_ids_trimmed = [
                out_ids[len(in_ids) :]
                for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
            ]

            output_text = self._processor.batch_decode(
                generated_ids_trimmed,
                skip_special_tokens=True,
                clean_up_tokenization_spaces=False,
            )[0]

            try:
                parsed_output = json.loads(output_text)
            except json.JSONDecodeError:
                parsed_output = {"raw_extraction": output_text}

            return PredictionResult(
                model_name=_MODEL_NAME,
                model_version=_MODEL_VERSION,
                prediction=parsed_output,
                confidence=1.0,
            )

        except Exception as exc:
            raise RuntimeError(f"NuExtract inference failed: {exc}") from exc

    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "text": {"type": "string"},
                "image": {"type": "ndarray"},
                "template": {"type": ["object", "string"]},
            },
            "anyOf": [{"required": ["text"]}, {"required": ["image"]}],
        }

    def output_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "additionalProperties": True,
        }

    def _ensure_loaded(self) -> None:
        if self._model is None or self._processor is None:
            raise ModelLoadError(_MODEL_NAME, "Model is not loaded.")
