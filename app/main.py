import logging
import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.job_control import JobQueue, JobScheduler
from app.routers import job_router
from app.runnables import DummyTrainer, RunnableFactory
from app.runners import ProcessRunnerFactory

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def detect_gpu_slots(default: int = 1) -> int:
    """Detect the number of GPU slots available for running jobs."""
    if "GPU_SLOTS" in os.environ:
        try:
            return max(1, int(os.environ["GPU_SLOTS"]))
        except ValueError:
            pass
    return default


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """Lifespan context manager to handle startup and shutdown events."""
    q = JobQueue()
    trainer_factory = RunnableFactory(DummyTrainer)
    process_runner_factory = ProcessRunnerFactory(trainer_factory)
    job_scheduler = JobScheduler(
        jobs_queue=q, runner_factory=process_runner_factory, max_parallel_jobs=detect_gpu_slots()
    )
    await job_scheduler.start()

    app.state.queue = q

    # TODO: restore jobs from DB to queue

    yield

    # TODO: persist pending jobs from queue to DB
    await job_scheduler.stop()

    logger.info("Application shutdown completed")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(job_router.router)

    @app.get("/health")
    async def health_check() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="localhost",
        port=5001,
    )
