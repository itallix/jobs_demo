from fastapi import Request

from app.job_control import JobQueue


def get_queue(request: Request) -> JobQueue:
    return request.app.state.queue
