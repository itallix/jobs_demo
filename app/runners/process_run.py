import asyncio
import contextlib
import multiprocessing as mp
from multiprocessing.connection import Connection
from multiprocessing.synchronize import Event
from typing import Callable
from typing import Iterator

from app.models import Job
from app.trainers.events import Done, Failed, TrainingEvent
from app.trainers.base import Trainer, TrainerFactory


class ProcessRun:
    """Owns the child Process+IPC and translates to domain events."""

    def __init__(self, ctx: mp.context.SpawnContext, trainer_factory: Callable[[], Trainer], job: Job):
        self._ctx = ctx
        self._trainer_factory = trainer_factory
        self._job = job
        self._parent, self._child = ctx.Pipe(duplex=False)
        self._cancel = ctx.Event()
        self._proc: mp.Process | None = None

    def start(self) -> "ProcessRun":
        self._proc = self._ctx.Process(
            target=_entrypoint,
            args=(self._trainer_factory, self._job.model_dump_json(), self._child, self._cancel),
            name=f"trainer-{self._job.id}"
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

    async def stop(self, timeout: float = 6.0) -> None:
        if self._proc is None:
            return

        self._cancel.set()
        step = 0.2

        for _ in range(int(timeout/step)):
            if not self._proc.is_alive():
                return
            await asyncio.sleep(step)

        if self._proc.is_alive():
            self._proc.kill()

        await asyncio.to_thread(self._proc.join, timeout=1.0)

        self._parent.close()


def _entrypoint(get_trainer: TrainerFactory, job_payload: str, conn: Connection, cancel_event: mp.synchronize.Event) -> None:
    from app.trainers.events import Progress, Done, Cancelled, Failed
    import traceback
    class CancelledExc(Exception): pass

    trainer = get_trainer()
    job = Job.model_validate_json(job_payload)

    def report(p: float):
        conn.send(Progress(float(p)))

    # alt: another possible solution is to run the heartbeat in a separate daemon thread at a set interval, so it isn’t
    # coupled to the training process.
    def heartbeat():
        if cancel_event.is_set():
            raise CancelledExc()

    try:
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

    def for_job(self, job: Job) -> ProcessRun:
        return ProcessRun(self._ctx, self._trainer_factory, job)
