# Vision Service

Vision Service is the brain of the platform, located in `platform/vision/`.
It is dynamically orchestrated by the `galadril-pipeline` library.
It relies on the `galadril-inference` library to standardize calls to ML
algorithms.

TODO: explain how to extend `galadril-inference` and `galadril-vision`.

## DAG Construction

Service builds a DAG from the `pipeline.yaml` file. 
* It validates that no circular dependencies exist.
* It calculates the exact topological order required to execute models.

## Dynamic Model Loading
Models are not hardcoded. Service uses Python's `importlib` to instantiate the
exact classes defined in the configuration.
Model weights are automatically pulled from S3 into memory before processing
begins.

## Message Routing Loop
1. The service polls batches of messages from Kafka.
2. It identifies the origin (`source_id`).
3. It asks the DAG: *"Which model steps require this source as input?"*
4. It passes the data to the model.
5. Once the model outputs a prediction, the service asks the DAG: *"Who needs
    this output next?"*
6. If no one needs it, the data has reached the end of the pipeline (a Sink).
