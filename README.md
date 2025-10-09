# Async Jobs Scheduler

Job scheduler implemented in Python using `FastAPI` and `asyncio`. 
It allows to submit, track, and manage jobs concurrently.
Job execution context is separated from job management, allowing to plug in different training backends (e.g., OTX, PyTorch).

## Features

- **Job Submission**: Submit jobs via a REST API.
- **Job Tracking**: Query job status, progress, and results.
- **Streaming Updates**: Receive real-time job status updates via Server-Sent Events (SSE).
- **Concurrent Execution**: Jobs are processed concurrently, with configurable GPU slot limits.
- **Extensible Trainer**: Plug in custom training logic (e.g., OTX, PyTorch).

## API Endpoints

- `POST /api/jobs` — Submit a new job.
- `GET /api/jobs` — List all jobs.
- `GET /api/jobs/{job_id}` — Get details of a specific job.
- `PATCH /api/jobs/{job_id}/cancel` — Cancel a specific job.
- `GET /api/jobs/{job_id}/stream` — Stream job status updates.

## Quick Start

1. **Install dependencies**  
   Requires Python 3.13+.
   ```sh
   uv sync
   ```

2. **Run the server**
   ```sh
   uv run -m app.main
   ```

3. **Submit a job**
   Use `curl` or any HTTP client:
   ```sh
   curl -X POST http://localhost:5001/api/jobs \
     -H "Content-Type: application/json" \
     -d '{"id": "3fb85f64-5717-4562-b3fc-2c963f66afa6"}'
   ```

## Configuration

- Set the `GPU_SLOTS` environment variable to control the number of concurrent jobs.
