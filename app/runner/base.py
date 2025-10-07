from typing import Protocol, Iterator

from app.training.events import TrainingEvent


class Runner(Protocol):
    """
    Protocol for a training job runner.

    Represents an interface for starting, stopping, and monitoring the progress of a training job.
    """

    def start(self) -> "Runner": ...
    def events(self) -> Iterator[TrainingEvent]: ...
    async def stop(self, timeout: float | None = None) -> None: ...


class RunnerFactory(Protocol):
    """
    Protocol for a factory that creates Runner instances for specific jobs.
    """

    def for_job(self, job) -> Runner: ...
