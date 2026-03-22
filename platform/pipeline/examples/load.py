import sys
from pathlib import Path
from galadril_pipeline import (
    PipelineParser,
    CircularDependencyError,
    MissingDependencyError,
)


def main():
    config_path = (
        Path(__file__).parent.parent.parent.parent
        / "examples"
        / "pipeline.yaml"
    )

    if not config_path.exists():
        print(f"Configuration file not found at {config_path.absolute()}")
        return

    try:
        pipeline_graph = PipelineParser.from_yaml(config_path)

        kafka_topics = pipeline_graph.get_kafka_topics()
        print(f"Topics from config are: {', '.join(kafka_topics)}")

        # Get the ordered execution plan (topological sort).
        execution_plan = pipeline_graph.get_execution_plan()

        print("\nExecution plan:")
        for i, step in enumerate(execution_plan, 1):
            print(f"  {i}. Step: {step.step}")
            print(f"     Type: {step.type}")
            print(f"     Inputs: {step.input_from}")
            if step.model:
                print(f"     Model: {step.model}")
            print("\n")

    except CircularDependencyError as e:
        print(f"Circular loop detected: {e}")
        sys.exit(1)
    except MissingDependencyError as e:
        print(f"A step refers to a non-existent source or step: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error during parsing: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
