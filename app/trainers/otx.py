from app.models import Job
from app.training.base import HeartbeatFn, ReportFn, Trainer


class OTXTrainer(Trainer):
    def train(self, job: Job, report: ReportFn, heartbeat: HeartbeatFn) -> None:
        raise NotImplementedError
