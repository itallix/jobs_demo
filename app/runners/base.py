from collections.abc import Iterator
from typing import Protocol

from app.models import Job
from app.trainers.events import TrainingEvent


class Runner(Protocol):
    """
    Protocol for a training job runner.

    Represents an interface for starting, stopping, and monitoring the progress of a training job.
    """

    def start(self) -> "Runner": ...
    def events(self) -> Iterator[TrainingEvent]: ...
    async def stop(self, wait_for: float = 6.0, kill_timeout: float = 1.0) -> None: ...


class RunnerFactory(Protocol):
    """
    Protocol for a factory that creates Runner instances for specific jobs.
    """

    def for_job(self, job: Job) -> Runner: ...
