import asyncio
import contextlib
import multiprocessing as mp
from collections.abc import Callable, Iterator
from multiprocessing.connection import Connection
from multiprocessing.context import SpawnProcess
from multiprocessing.synchronize import Event

from app.models import Job
from app.runners.base import Runner
from app.trainers.base import Trainer, TrainerFactory
from app.trainers.events import Done, Failed, Started, TrainingEvent


class ProcessRun:
    """Owns the child Process+IPC and translates to domain events."""

    def __init__(self, ctx: mp.context.SpawnContext, trainer_factory: Callable[[], Trainer], job: Job):
        self._ctx = ctx
        self._trainer_factory = trainer_factory
        self._job = job
        self._parent, self._child = ctx.Pipe(duplex=False)
        self._cancel = ctx.Event()
        self._proc: SpawnProcess | None = None

    def start(self) -> "ProcessRun":
        self._proc = self._ctx.Process(
            target=_entrypoint,
            args=(self._trainer_factory, self._job.model_dump_json(), self._child, self._cancel),
            name=f"trainer-{self._job.id}",
        )
        self._proc.start()
        self._child.close()
        return self

    def events(self) -> Iterator[TrainingEvent]:
        """Blocking iterator; the control plane decides how to multiplex."""
        try:
            while True:
                msg = self._parent.recv()  # blocks
                yield msg  # msg is already a TrainerEvent instance (Progress/Done/...)
        except EOFError:
            # Child exited; infer outcome
            code = self._proc.exitcode if self._proc else 1
            yield Done() if code == 0 else Failed(f"process exit {code}")
        finally:
            self._parent.close()

    async def stop(self, wait_for: float = 6.0, kill_timeout: float = 1.0) -> None:
        """Stop the training process.

        Args:
            wait_for: How long to wait for graceful shutdown (seconds)
            kill_timeout: How long to wait for process.join() after killing (seconds)
        """
        if self._proc is None:
            return

        self._cancel.set()

        try:
            await asyncio.to_thread(self._proc.join, timeout=wait_for)
        except TimeoutError:
            if self._proc.is_alive():
                self._proc.kill()
                # Give it a final chance to clean up
                await asyncio.to_thread(self._proc.join, timeout=kill_timeout)

        self._parent.close()


def _entrypoint(get_trainer: TrainerFactory, job_payload: str, conn: Connection, cancel_event: Event) -> None:
    import traceback

    from app.trainers.events import Cancelled, Done, Failed, Progress

    class CancelledExc(Exception):
        pass

    trainer = get_trainer()
    job = Job.model_validate_json(job_payload)

    def report(p: float):
        conn.send(Progress(float(p)))

    # alt: another possible solution is to run the heartbeat in a separate daemon thread at a set interval, so it is not
    # coupled to the training process.
    def heartbeat():
        if cancel_event.is_set():
            raise CancelledExc

    try:
        conn.send(Started())
        trainer.train(job, report, heartbeat)
        conn.send(Done())
    except CancelledExc:
        conn.send(Cancelled())
    except Exception:
        conn.send(Failed(traceback.format_exc()))
    finally:
        with contextlib.suppress(Exception):
            conn.close()


class ProcessRunnerFactory:
    """Process-based infra with spawned context"""

    def __init__(self, trainer_factory: Callable[[], Trainer]) -> None:
        # consider using native context for python 3.14 due to upgrade to 'fork_server' model
        self._ctx = mp.get_context("spawn")
        self._trainer_factory = trainer_factory

    def for_job(self, job: Job) -> Runner:
        return ProcessRun(self._ctx, self._trainer_factory, job)
