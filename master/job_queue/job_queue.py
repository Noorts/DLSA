from uuid import UUID, uuid4

from fastapi import HTTPException

from api_models import JobRequest
from job_queue.queued_job import QueuedJob
from utils.singleton import Singleton


class JobNotFoundException(HTTPException):
    def __init__(self, job_id: UUID):
        super().__init__(status_code=404, detail=f"Job with id {job_id} not found")


class JobQueue(Singleton):
    def __init__(self):
        super().__init__()
        self._jobs: dict[UUID, QueuedJob] = {}

    def add_job_to_queue(self, request: JobRequest) -> QueuedJob:
        job_id = uuid4()
        self._jobs[job_id] = QueuedJob(request=request, completed_sequences={}, sequences_in_progress=[], id=job_id)
        return self._jobs[job_id]

    def unfinished_jobs(self) -> list[QueuedJob]:
        return [job for job in self._jobs.values() if not job.done()]

    def jobs_with_unassigned_sequences(self) -> list[QueuedJob]:
        jobs: list[QueuedJob] = []

        for job in self._jobs.values():
            if not job.done() and len(job.sequences_in_progress) + len(job.completed_sequences) < len(
                job.request.queries
            ):
                jobs.append(job)
        return jobs

    def get_job_by_id(self, job_id: UUID) -> QueuedJob:
        job = self._jobs.get(job_id)
        if not job:
            raise JobNotFoundException(job_id)
        return job

    def delete_job_by_id(self, job_id: UUID):
        self.get_job_by_id(job_id)
        del self._jobs[job_id]
