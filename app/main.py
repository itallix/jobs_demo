import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
import os

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.job_queue import JobsQueue
from app.job_scheduler import JobScheduler
from app.training import DummyTrainer, TrainerFactory
from app.runner import ProcessRunnerFactory
from app.routers import job_router

logger = logging.getLogger(__name__)


def detect_gpu_slots(default: int = 1) -> int:
    if "GPU_SLOTS" in os.environ:
        try:
            return max(1, int(os.environ["GPU_SLOTS"]))
        except ValueError:
            pass
    return default


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    q = JobsQueue()
    trainer_factory = TrainerFactory(DummyTrainer)
    process_runner_factory = ProcessRunnerFactory(trainer_factory)
    job_scheduler = JobScheduler(jobs_queue=q, runner_factory=process_runner_factory, max_parallel_jobs=detect_gpu_slots())
    await job_scheduler.start()

    app.state.queue = q

    # TODO: restore jobs from DB to queue

    yield

    # TODO: persist pending jobs from queue to DB
    await job_scheduler.stop()

    logger.info("Application shutdown completed")



def create_app() -> FastAPI:
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
