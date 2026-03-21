"""Entry point for galadril-vision pipeline."""

import argparse
import asyncio
import signal
import sys
import structlog

from galadril_vision.common.config import VisionConfig
from galadril_vision.config.loader import load_pipeline_config
from galadril_vision.pipeline.runner import VisionPipeline


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Galadril Vision pipeline")
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to pipeline.yaml",
    )
    return parser.parse_args()


async def preload_models(config: VisionConfig):
    """Warm up and load inference models before Ray workers run."""
    from galadril_inference import InferenceEngine
    from galadril_inference.storage import S3Loader

    logger = structlog.get_logger("model_warmup")
    loader = S3Loader(
        bucket=config.inference.bucket,
        prefix=config.inference.prefix,
        endpoint_url=config.inference.endpoint_url,
    )

    engine = InferenceEngine(loader=loader)

    model_names = set()
    if config.pipeline_config and config.pipeline_config.pipeline:
        for step in config.pipeline_config.pipeline:
            if step.type == "inference" and step.model:
                if "face_recognition" in step.model.lower():
                    model_names.add("face_recognition")
                else:
                    model_names.add(step.model.split(".")[-1].lower())
    else:
        logger.warning("no_pipeline_config_found", fallback="face_recognition")
        model_names.add("face_recognition")

    for model_name in model_names:
        try:
            engine.load_model(model_name)
            logger.info("model_preloaded", model=model_name, status="READY")
        except Exception as exc:
            logger.error(
                "model_preload_failed", model=model_name, error=str(exc)
            )

    ready = engine.ready_models()
    logger.info("models_ready", model_list=ready)
    return engine


async def main():
    logger = structlog.get_logger("main")
    args = parse_args()

    config = VisionConfig()

    if args.config:
        try:
            pipeline_cfg = load_pipeline_config(args.config)
            config.pipeline_config = pipeline_cfg

            config.kafka.bootstrap_servers = ",".join(
                pipeline_cfg.connectors.kafka.brokers
            )
            config.kafka.schema_registry = str(
                pipeline_cfg.connectors.kafka.schema_registry
            )
            config.kafka.group_id = pipeline_cfg.connectors.kafka.consumer_group

            if pipeline_cfg.connectors.s3:
                config.image_store.endpoint_url = str(
                    pipeline_cfg.connectors.s3.endpoint
                )

            if pipeline_cfg.connectors.postgres:
                pg = pipeline_cfg.connectors.postgres
                config.postgres.dsn = f"postgresql://{pg.user}:{pg.password}@{pg.host}/{pg.database}"

            logger.info(
                "pipeline_loaded",
                name=pipeline_cfg.name,
                sources=[s.topic for s in pipeline_cfg.sources],
                steps=[s.step for s in pipeline_cfg.pipeline],
            )
        except Exception as exc:
            logger.error("pipeline_config_error", error=str(exc))
            sys.exit(1)

    logger.info("config_loaded", config=config.model_dump(mode="json"))

    await preload_models(config)

    async with VisionPipeline(config) as pipeline:
        logger.info("pipeline_started")
        stop_event = asyncio.Event()

        def shutdown_handler(*_):
            logger.warning("shutdown_signal_received")
            stop_event.set()

        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, shutdown_handler)

        pipeline_task = asyncio.create_task(pipeline.run())

        await stop_event.wait()
        pipeline_task.cancel()
        try:
            await pipeline_task
        except asyncio.CancelledError:
            logger.info("pipeline_cancelled")

    logger.info("pipeline_stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as exc:
        structlog.get_logger("main").error("fatal_error", error=str(exc))
        sys.exit(1)
