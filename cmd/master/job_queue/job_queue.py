from uuid import UUID, uuid4

from fastapi import HTTPException

from ..api_models import JobRequest
from ..job_queue.queued_job import QueuedJob
from ..utils.singleton import Singleton


class JobNotFoundException(HTTPException):
    def __init__(self, job_id: UUID):
        super().__init__(status_code=404, detail=f"Job with id {job_id} not found")


class JobQueue(Singleton):
    def __init__(self):
        super().__init__()
        self._jobs: dict[UUID, QueuedJob] = {}

    def add_job_to_queue(self, request: JobRequest) -> QueuedJob:
        job_id = uuid4()
        self._jobs[job_id] = QueuedJob(request, {}, job_id)
        return self._jobs[job_id]

    def unfinished_jobs(self) -> list[QueuedJob]:
        return [job for job in self._jobs.values() if not job.done()]

    def get_job_by_id(self, job_id: UUID) -> QueuedJob:
        job = self._jobs.get(job_id)
        if not job:
            raise JobNotFoundException(job_id)
        return job