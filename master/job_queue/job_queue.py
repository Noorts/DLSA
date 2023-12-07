import logging
from uuid import UUID, uuid4

from fastapi import HTTPException

from master.api_models import JobRequest
from master.job_queue.queued_job import QueuedJob
from master.utils.singleton import Singleton

logger = logging.getLogger(__name__)


class JobNotFoundException(HTTPException):
    def __init__(self, job_id: UUID):
        super().__init__(status_code=404, detail=f"Job with id {job_id} not found")


class JobQueue(Singleton):
    def __init__(self):
        super().__init__()
        self._jobs: dict[UUID, QueuedJob] = {}

    def add_job_to_queue(self, request: JobRequest) -> QueuedJob:
        job_id = uuid4()
        logger.info(f"Adding job {job_id} to queue. Job has {len(request.queries)} queries")
        self._jobs[job_id] = QueuedJob(
            request=request,
            completed_sequences={},
            sequences_in_progress=set(),
            id=job_id,
            match_score=request.match_score,
            mismatch_penalty=request.mismatch_penalty,
            gap_penalty=request.gap_penalty,
        )
        return self._jobs[job_id]

    def unfinished_jobs(self) -> list[QueuedJob]:
        return [job for job in self._jobs.values() if not job.done()]

    def jobs_with_unassigned_sequences(self) -> list[QueuedJob]:
        jobs: list[QueuedJob] = []

        for job in self._jobs.values():
            if not job.done() and job.missing_sequences():
                jobs.append(job)
        return jobs

    def get_job_by_id(self, job_id: UUID) -> QueuedJob:
        job = self._jobs.get(job_id)
        if not job:
            raise JobNotFoundException(job_id)
        return job

    def delete_job_by_id(self, job_id: UUID):
        logger.info(f"Deleting job {job_id} from queue")
        self.get_job_by_id(job_id)
        del self._jobs[job_id]
