import asyncio
import contextlib
import logging
import threading

from app.job_control.capacity import Capacity
from app.job_control.queue import JobQueue
from app.models import Job
from app.runners.base import Runner, RunnerFactory
from app.trainers.events import Cancelled, Done, Failed, Progress, Started

logger = logging.getLogger(__name__)


class JobScheduler:
    """
    Event-driven control plane for jobs.

    Runs the training job in a separate context and handles communication with it via domain events.

    Note: Job orchestration is performed using asyncio to keep the event loop responsive.
    Training itself runs in a context defined by runner factory:
        - process-based runner make sure CPU-bound tasks do not block the event loop and crashes in training do not
        affect the main application.
    """

    def __init__(self, jobs_queue: JobQueue, runner_factory: RunnerFactory, max_parallel_jobs: int) -> None:
        self._jobs_q = jobs_queue
        self._runner_factory = runner_factory
        self._capacity = Capacity(max_parallel_jobs)
        self._running = False
        self._supervisor_task: asyncio.Task | None = None
        self._tasks: set[asyncio.Task] = set()

    async def start(self) -> None:
        self._running = True
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
                job = await self._jobs_q.next_runnable()
                if not job:
                    continue
                logger.info("Starting job", extra={"job_id": job.id})
                self._start_job(job)
            except Exception:
                logger.exception("Exception during supervise loop")
            await asyncio.sleep(0.5)

    def _start_job(self, job: Job) -> None:
        task = asyncio.create_task(self._run_job(job))
        self._tasks.add(task)
        task.add_done_callback(lambda t: (self._tasks.discard(t)))

    async def _run_job(self, job: Job) -> None:
        async with self._capacity.permit():
            job_run = self._runner_factory.for_job(job)
            event_q: asyncio.Queue = asyncio.Queue()

            # Set up event pumping and cancellation monitoring
            cancel_task = self._setup_job_execution(job, job_run, event_q)

            try:
                # Handle events from the job runner
                await self._handle_job_events(job, event_q)
            finally:
                cancel_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await cancel_task

            logger.info("Job completed", extra={"job_id": job.id, "job_status": job.status})

    def _setup_job_execution(self, job: Job, job_run: Runner, event_q: asyncio.Queue) -> asyncio.Task:
        """Set up event pumping thread and cancellation monitoring task."""
        loop = asyncio.get_running_loop()

        def _pump():
            for ev in job_run.events():
                asyncio.run_coroutine_threadsafe(event_q.put(ev), loop)
            asyncio.run_coroutine_threadsafe(event_q.put(None), loop)

        async def _cancel():
            """Watch for job cancellation requests and trigger graceful shutdown."""
            while True:
                if self._jobs_q.is_cancelling(job.id):
                    await job_run.stop()
                    return
                await asyncio.sleep(0.2)

        threading.Thread(target=_pump, daemon=True).start()
        cancel_task = asyncio.create_task(_cancel())
        job_run.start()

        return cancel_task

    @staticmethod
    async def _handle_job_events(job: Job, event_q: asyncio.Queue) -> None:
        """Handle events from the job runner and update job state accordingly."""
        while True:
            evt = await event_q.get()
            if evt is None:
                break

            match evt:
                case Started():
                    job.start()
                case Progress(value=v):
                    job.advance(v)
                case Done():
                    job.finish()
                    break
                case Cancelled():
                    job.cancel()
                    break
                case Failed(details=d):
                    job.fail(msg=d)
                    break
                case _:
                    logger.warning("Unknown trainer event: %s", evt)
