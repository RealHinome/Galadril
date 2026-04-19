from __future__ import annotations

import importlib
from typing import Any


def import_string(path: str) -> Any:
    """Dynamically import a class/module from a string path."""
    module_name, class_name = path.rsplit(".", 1)
    module = importlib.import_module(module_name)
    return getattr(module, class_name)


def build_model(model_path: str, **kwargs: Any) -> Any:
    """Instantiate a model dynamically (useful for local sync execution)."""
    model_cls = import_string(model_path)
    return model_cls(**kwargs)
