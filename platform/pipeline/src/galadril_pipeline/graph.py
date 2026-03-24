from typing import List, Dict, Set
from .config import PipelineConfig
from galadril_pipeline.models.pipeline import PipelineStep


class CircularDependencyError(Exception):
    pass


class MissingDependencyError(Exception):
    pass


class PipelineGraph:
    def __init__(self, config: PipelineConfig):
        self.config = config
        self._validate_and_build_graph()

    def _validate_and_build_graph(self):
        self.valid_nodes = {s.id for s in self.config.sources}
        self.steps_by_name: Dict[str, PipelineStep] = {
            step.step: step for step in self.config.pipeline
        }

        self.valid_nodes.update(self.steps_by_name.keys())

        self.graph: Dict[str, List[str]] = {}
        for step in self.config.pipeline:
            for dep in step.input_from:
                if dep not in self.valid_nodes:
                    raise MissingDependencyError(
                        f"Step '{step.step}' depends on '{dep}' which does not exist."
                    )
            self.graph[step.step] = step.input_from

    def get_kafka_topics(self) -> List[str]:
        """Returns the list of all Kafka topics to listen to."""
        return list({source.topic for source in self.config.sources})

    def get_execution_plan(self) -> List[PipelineStep]:
        """
        Returns the topological execution order of the pipeline steps.
        """
        visited: Set[str] = set()
        temp_visited: Set[str] = set()
        order: List[str] = []

        def visit(node: str):
            if node in temp_visited:
                raise CircularDependencyError(
                    f"Loop detected involving node '{node}'"
                )
            if node in visited:
                return

            temp_visited.add(node)

            if node in self.graph:
                for dep in self.graph[node]:
                    visit(dep)

            temp_visited.remove(node)
            visited.add(node)

            if node in self.steps_by_name:
                order.append(node)

        for step_name in self.graph.keys():
            if step_name not in visited:
                visit(step_name)

        return [self.steps_by_name[step_name] for step_name in order]
