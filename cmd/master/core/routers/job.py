from fastapi import APIRouter

from ..models import JobRequest, JobId, JobStatus, JobResult

job_router = APIRouter()


# submit a job to the job queue, returns a job id (for client)
@job_router.post("/job/format/internal")
def submit_job(body: JobRequest) -> JobId:
    pass


# returns the state of a job (for a client)
@job_router.get("/job/{job_id}/status")
def get_job(job_id: str) -> JobStatus:
    pass


# returns the state of a job (for a client)
@job_router.get("/job/{job_id}/result")
def get_job(job_id: str) -> JobResult:
    pass
