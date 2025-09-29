import asyncio
import logging
from typing import Callable, Protocol

from app.models import Job


logger = logging.getLogger(__name__)


class Trainer(Protocol):
    async def train(self, job: Job, report: Callable[[float], None]) -> None: ...


class OTXTrainer(Trainer):

    async def train(self, job: Job, report: Callable[[float], None]) -> None:
        logger.info("Training with OpenVINO: %s", job.id)
        # Implement OTX training logic here

        # Simulate training with progress reporting
        step_count = 10
        for i in range(step_count):
            await asyncio.sleep(1)
            logger.info("OpenVINO training step %d/%d for job %s", i + 1, step_count, job.id)
            report(10.0 * (i + 1))

        logger.info("Completed OpenVINO training: %s", job.id)
