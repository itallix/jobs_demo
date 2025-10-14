from fastapi import Request

from app.job_control import JobQueue


def get_queue(request: Request) -> JobQueue:
    """Get the job queue from the application state."""
    return request.app.state.queue
