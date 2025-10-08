import logging
import time

from app.models import Job
from app.trainers.base import HeartbeatFn, ReportFn, Trainer

logger = logging.getLogger(__name__)


class DummyTrainer(Trainer):
    def train(self, job: Job, report: ReportFn, heartbeat: HeartbeatFn) -> None:
        logger.info("Training started. Job ID: %s", job.id)
        # Implement OTX training logic here

        # Simulate training with progress reporting
        step_count = 10
        for i in range(step_count):
            time.sleep(1)
            logger.info("Training step %d/%d for job %s", i + 1, step_count, job.id)
            report(10.0 * (i + 1))
            heartbeat()

        logger.info("Completed training: %s", job.id)
