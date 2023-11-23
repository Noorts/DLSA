from uuid import UUID

from fastapi import HTTPException

from ..models import JobRequest
from ..queue.queued_job import QueuedJob
from ..utils.singleton import Singleton


class JobNotFound(HTTPException):
    def __init__(self, job_id: UUID):
        super().__init__(status_code=404, detail=f"Job with id {job_id} not found")


class JobQueue(Singleton):
    def __init__(self):
        self._jobs: dict[UUID, QueuedJob] = {}

    def queue_job(self, job: JobRequest):
        self._jobs[job.id] = QueuedJob(job, {})

    def unfinished_jobs(self) -> list[QueuedJob]:
        return [job for job in self._jobs.values() if not job.done()]

    def get_job_by_id(self, job_id: UUID) -> QueuedJob:
        job = self._jobs.get(job_id)
        if not job:
            raise JobNotFound(job_id)
        return job
