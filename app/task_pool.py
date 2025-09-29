import asyncio
import contextlib
import logging

from app.job_queue import JobsQueue
from app.trainer import Trainer
from app.models import Job

logger = logging.getLogger(__name__)


class TaskPool:

    def __init__(self, q: JobsQueue, trainer: Trainer, gpu_slots: int) -> None:
        self._q = q
        self._trainer = trainer
        self._sema = asyncio.Semaphore(max(1, gpu_slots))
        self._running = True
        self._supervisor_task: asyncio.Task | None = None
        self._tasks: set[asyncio.Task] = set()

    async def start(self) -> None:
        self._supervisor_task = asyncio.create_task(self._supervise_loop(), name="supervisor")

    async def stop(self) -> None:
        self._running = False
        if self._supervisor_task:
            self._supervisor_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._supervisor_task
        await asyncio.gather(*self._tasks, return_exceptions=True)

    async def _supervise_loop(self) -> None:
        while self._running:
            try:
                while self._sema._value > 0:
                    job = await self._q.next()
                    await self._dispatch(job)
            except Exception:
                logger.exception("Exception during supervise loop")
            await asyncio.sleep(0.5)

    async def _dispatch(self, job: Job) -> None:
        await self._sema.acquire()
        job.start()
        task = asyncio.create_task(self._run_job(job))
        self._tasks.add(task)
        task.add_done_callback(lambda t: (self._tasks.discard(t), self._sema.release()))

    async def _run_job(self, job: Job) -> None:
        def report(p: float) -> None:
            job.advance(p)

        try:
            await self._trainer.train(job, report)
        except Exception as e:
            logger.exception(f"Job {job.id} failed")
            job.fail(str(e))
            return

        job.finish()
