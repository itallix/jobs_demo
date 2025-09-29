from fastapi import Request

from app.job_queue import JobsQueue


def get_queue(request: Request) -> JobsQueue:
    return request.app.state.queue
