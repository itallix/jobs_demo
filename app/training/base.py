from typing import Callable, Protocol

from app.models import Job


ReportFunction = Callable[[float], None]
HeartbeatFunction = Callable[[], None]


class Trainer(Protocol):
    """Trainer interface."""

    def train(self, job: Job, report: ReportFunction, heartbeat: HeartbeatFunction) -> None: ...


class TrainerFactory:
    def __init__(self, trainer_cls: type[Trainer]) -> None:
        self._trainer_cls = trainer_cls

    def __call__(self) -> Trainer:
        return self._trainer_cls()
