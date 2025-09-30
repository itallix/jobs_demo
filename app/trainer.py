import asyncio
import logging
from typing import Callable, Protocol

from app.models import Job


logger = logging.getLogger(__name__)


ReportFunction = Callable[[float], None]
HeartbeatFunction = Callable[[], None]


class Trainer(Protocol):
    async def train(self, job: Job, report: ReportFunction, heartbeat: HeartbeatFunction) -> None: ...


class OTXTrainer(Trainer):

    async def train(self, job: Job, report: ReportFunction, heartbeat: HeartbeatFunction) -> None:
        logger.info("Training with OTX: %s", job.id)
        # Implement OTX training logic here

        # Simulate training with progress reporting
        step_count = 10
        for i in range(step_count):
            await asyncio.sleep(1)
            logger.info("OTX training step %d/%d for job %s", i + 1, step_count, job.id)
            report(10.0 * (i + 1))
            heartbeat()

        logger.info("Completed OTX training: %s", job.id)
