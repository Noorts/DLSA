from uuid import UUID

from fastapi import APIRouter, HTTPException

from master.api_models import (
    JobRequest,
    JobId,
    JobStatus,
    JobResult,
    JobResultCombination,
)
from master.job_queue.job_queue import JobQueue
from master.settings import SETTINGS

job_router = APIRouter(tags=["external"])
_job_queue = JobQueue()


# submit a job to the job job_queue, returns a job id (for client)
@job_router.post("/job/format/json")
def submit_job(body: JobRequest) -> JobId:
    job = _job_queue.add_job_to_queue(body)
    return JobId(id=job.id)


# returns the state of a job (for a client)
@job_router.get("/job/{job_id}/status")
def get_job(job_id: UUID) -> JobStatus:
    job = _job_queue.get_job_by_id(job_id)
    return JobStatus(state=job.state, progress=job.percentage_done)


# returns the state of a job (for a client)
@job_router.get("/job/{job_id}/result")
def get_job(job_id: UUID) -> JobResult:
    job = _job_queue.get_job_by_id(job_id)

    if job.state != "DONE":
        raise HTTPException(status_code=404, detail="Job not done yet")

    return JobResult(
        alignments=[
            JobResultCombination(
                combination=combination,
                alignment=alignment,
            )
            for combination, alignment in job.completed_sequences.items()
        ]
    )


@job_router.delete("/job/{job_id}")
def delete_job(job_id: UUID):
    """
    This is only intended for testing purposes.<br>
    Job deletion might have unwanted side effects, as workers might still be working on the job and work packages are
    not cleaned up.
    """
    if not SETTINGS.enable_job_deletion:
        raise HTTPException(status_code=403, detail="Job deletion is disabled")

    _job_queue.delete_job_by_id(job_id)
