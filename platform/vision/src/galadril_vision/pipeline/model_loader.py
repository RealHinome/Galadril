from __future__ import annotations

import importlib


def import_string(path: str):
    module_name, class_name = path.rsplit(".", 1)
    module = importlib.import_module(module_name)
    return getattr(module, class_name)


def build_model(model_path: str, **kwargs):
    model_cls = import_string(model_path)
    return model_cls(**kwargs)
