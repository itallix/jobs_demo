import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
import os

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.job_queue import JobsQueue
from app.task_pool import TaskPool
from app.trainer import OTXTrainer
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
    trainer = OTXTrainer()
    pool = TaskPool(q=q, trainer=trainer, gpu_slots=detect_gpu_slots())
    await pool.start()

    app.state.queue = q

    # TODO: restore jobs from DB to queue

    yield

    # TODO: persist pending jobs from queue to DB
    await pool.stop()

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
