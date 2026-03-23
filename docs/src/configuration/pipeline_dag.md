# Pipeline (Steps)

`pipeline` defines a DAG for processing. It connects data sources to ML models,
and ML models to other ML models.

## Step Definition

| Field | Description |
|---|---|
| `step` | Unique name for this processing node (e.g., `face_detection`). |
| `type` | Usually `inference` for Galadril. |
| `model` | The fully qualified Python class path. |
| `artifact_path` | Where the model weights are stored on S3. |
| `input_from` | **Array of IDs**. Defines the dependencies of this step. |
| `params` | Key-Value pairs passed to the model's constructor. |

## Understanding `input_from`

The `input_from` array is the most important field. It tells the Python
orchestrator where to get the data for this step.

You can reference:
1. **A Source ID**: To process raw data directly from Kafka.
2. **Another Step ID**: To chain models together.

### Example: Chaining Models
In this example, the Face Recognition model waits for raw images, and the
Database Storage step waits for the Face Recognition step to finish.

```yaml
pipeline:
  # Step 1: Detect faces from raw images
  - step: face_detection
    type: inference
    model: my_models.FaceRecognition
    input_from: [image_source] # References a Source ID
    params:
      threshold: 0.85

  # Step 2: Store results in the database
  - step: database_sink
    type: storage
    model: my_models.PostgresSink
    input_from: [face_detection] # References the previous Step ID
```
