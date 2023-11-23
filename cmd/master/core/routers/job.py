from uuid import UUID

from fastapi import APIRouter

from ..models import JobRequest, JobId, JobStatus, JobResult
from ..queue.job_queue import JobQueue

job_router = APIRouter()
_job_queue = JobQueue()


# submit a job to the job queue, returns a job id (for client)
@job_router.post("/job/format/internal")
def submit_job(body: JobRequest) -> JobId:
    job = _job_queue.queue_job(body)
    return JobId(id=job.id)


# returns the state of a job (for a client)
@job_router.get("/job/{job_id}/status")
def get_job(job_id: UUID) -> JobStatus:
    job = _job_queue.get_job_by_id(job_id)
    return JobStatus(id=job.request.id, state=job.state, progress=job.completed_percentage())


# returns the state of a job (for a client)
@job_router.get("/job/{job_id}/result")
def get_job(job_id: UUID) -> JobResult:
    job = _job_queue.get_job_by_id(job_id)
    return JobResult(alignments=[*job.completed_sequences.items()])
