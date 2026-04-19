## Models

The system supports several pre-trained models out of the box. These can be
referenced using their respective `_MODEL_NAME` identifiers.

| Model Name | Description | Research Paper |
| :--- | :--- | :--- |
| **face_recognition** | Face analysis and identification via InsightFace (Buffalo). |  |
| **gliner2** | Joint entity and relation extraction via GLiNER2. | [Arxiv](https://arxiv.org/abs/2507.18546) |
| **got_ocr** | Unified visual text processing with GOT-OCR 2.0. | [Arxiv](https://arxiv.org/abs/2409.01704) |
| **grounded_sam** | Zero-shot object detection and segmentation (Grounded-SAM). | [Arxiv](https://arxiv.org/abs/2401.14159) |
| **nuextract** | Template-based structured JSON information extraction. | [HF](https://huggingface.co/numind/NuExtract-2.0-2B) |
| **owlv2** | Open-world object detection and localization. | [Arxiv](https://arxiv.org/abs/2306.09683) |
| **siglip2** | Advanced vision-language model for image-text understanding. | [Arxiv](https://arxiv.org/abs/2502.14786) |
| **timesfm_forecast** | Time-series foundation model for versatile forecasting. | [Arxiv](https://arxiv.org/abs/2310.10688) |
| **whisper** | Multilingual speech-to-text with diarization and embeddings. | [Arxiv](https://arxiv.org/abs/2212.04356) |

---

## Model Details

### 1. Face Recognition (`face_recognition`)
Performs facial detection, alignment, and embedding extraction.

* **Inputs:**
    * `action` (Required): The inference action to perform (from `FaceAction`).
    * `image` (Required): BGR image as numpy array `(H, W, 3)`.
* **Outputs:**
    * `faces_count`: Number of detected faces.
    * `faces`: List of objects containing `bbox`, `keypoints`, `confidence`, and the 512-d `embedding`.

### 2. GLiNER2 (`gliner2`)
Zero-shot model for joint entity and relation extraction from text.

* **Inputs:**
    * `text` (Required): The input string for extraction.
    * `entities`: Dictionary mapping entity types to descriptions.
    * `relations`: Dictionary mapping relation types to descriptions.
* **Outputs:**
    * `entities`: Grouped list of extracted spans per entity type.
    * `relations`: List of objects with `source`, `target`, and `relation_type`.

### 3. GOT OCR (`got_ocr`)
General Object Role-playing OCR for high-quality text extraction.

* **Inputs:**
    * `image` / `images`: Single ndarray or list of images.
    * `action`: Specific OCR task (from `GotOcrAction`).
    * `format`: Boolean (default `True`) to maintain formatting.
    * `box`: Optional crop area `[x1, y1, x2, y2]`.
* **Outputs:**
    * `text`: The extracted string content.

### 4. Grounded SAM (`grounded_sam`)
Combines language understanding with precise image segmentation.

* **Inputs:**
    * `image` & `text` (Required): The source image and the prompt to segment.
    * `threshold`: Detection confidence (default `0.2`).
    * `return_masks`: Whether to return the binary segmentation masks.
    * *Note: Supports tiling for high-resolution images via `use_tiling`.*
* **Outputs:**
    * `total_objects`: Count of all detected instances.
    * `concepts`: Dictionary mapped by label containing `box`, `score`, and optionally `mask`.

### 5. NuExtract (`nuextract`)
Multimodal structured information extraction using a JSON template.

* **Inputs:**
    * `text` or `image` (Required): The source content to extract from.
    * `template`: A JSON structure or string defining the desired output schema.
* **Outputs:**
    * `prediction`: A structured JSON object following the provided template.

### 6. OWLv2 (`owlv2`)
Open-world localized vocabulary object detection.

* **Inputs:**
    * `image` & `text` (Required): Image and query labels.
    * `threshold`: Detection sensitivity (default `0.1`).
* **Outputs:**
    * `concepts`: Detailed instances per label with `box` and `score`.

### 7. SigLIP 2 (`siglip2`)
State-of-the-art vision-language model for creating shared embeddings.

* **Inputs:**
    * `action` (Required): `embed_image` or `embed_text`.
    * `image`: Required for image embedding.
    * `text`: Required for text embedding.
* **Outputs:**
    * `embedding`: Vector representation.
    * `embedding_dim`: Size of the vector.

### 8. TimesFM Forecast (`timesfm_forecast`)
Foundation model for time-series forecasting with external covariates.

* **Inputs:**
    * `history` (Required): List of numerical historical values.
    * `horizon`: Number of future steps to predict (default `24`).
    * `dynamic_numerical_covariates`: Optional dict for external regressors.
* **Outputs:**
    * `point_forecast`: The predicted mean values.
    * `quantiles`: Deciles (0.1 to 0.9) for uncertainty estimation.

### 9. Whisper (`whisper`)
Multilingual speech-to-text with advanced speaker diarization.

* **Inputs:**
    * `audio` (Required): Dict containing `waveform` (ndarray) and `sample_rate`.
    * `task`: `transcribe` or `translate` (default `transcribe`).
    * `language`: Optional ISO language code.
    * `enable_diarization`: Boolean to trigger speaker clustering and embeddings.
* **Outputs:**
    * `text`: Full transcript string.
    * `chunks`: Segments with `timestamp`, `text`, `speaker`, and `speaker_embedding`.
    * `language`: Detected or used language.
