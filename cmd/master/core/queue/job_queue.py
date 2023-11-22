from typing import Dict

from ..models import JobRequest
from ..queue.queued_job import QueuedJob
from ..utils.singleton import Singleton


class JobQueue(Singleton):
    def __init__(self):
        self._jobs: Dict[str, QueuedJob] = {}

    def queue_job(self, job: JobRequest):
        self._jobs[job.id] = QueuedJob(job, {})

    def unfinished_jobs(self) -> list[QueuedJob]:
        return [job for job in self._jobs.values() if not job.done()]

    def get_job_by_id(self, job_id: str) -> QueuedJob:
        return self._jobs[job_id]
