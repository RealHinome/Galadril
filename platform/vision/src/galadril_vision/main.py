"""Entry point for galadril-vision pipeline."""

import asyncio
import sys
import signal
import structlog

from galadril_vision.common.config import VisionConfig
from galadril_vision.pipeline.runner import VisionPipeline


def setup_logging():
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        cache_logger_on_first_use=True,
    )
    import logging

    logging.basicConfig(
        level="INFO",
        format="%(message)s",
        stream=sys.stdout,
    )


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
    model_names = [config.face_model_name]

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
    # setup_logging()
    logger = structlog.get_logger("main")

    config = VisionConfig()
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
