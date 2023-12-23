import logging
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, UploadFile, File

from master.api_models import (
    JobRequest,
    JobId,
    JobStatus,
    JobResult,
    JobResultCombination,
    MultipartJobRequest,
)
from master.job_queue.job_queue import JobQueue
from master.settings import SETTINGS

logger = logging.getLogger(__name__)
job_router = APIRouter(tags=["external"])
_job_queue = JobQueue()


# submit a job to the job job_queue, returns a job id (for client)
@job_router.post("/job/format/json")
async def submit_job(body: JobRequest) -> JobId:
    body.assert_required_sequences()
    job = _job_queue.add_job_to_queue(body)
    return JobId(id=job.id)


# submit a job to the job job_queue, returns a job id (for client)
@job_router.post("/job/format/multipart")
async def submit_multipart_job(body: MultipartJobRequest, sequences: Annotated[list[UploadFile], File()]) -> Any:
    file_dict = {}
    for sequence in sequences:
        try:
            sequence_uuid = UUID(sequence.filename)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid UUID in filename: {sequence.filename}")
        file_dict[sequence_uuid] = sequence.file.read().decode("utf-8")

    job_request = JobRequest(sequences=file_dict, **body.model_dump(mode="json")).assert_required_sequences()
    job = _job_queue.add_job_to_queue(job_request)
    return JobId(id=job.id)


# returns the state of a job (for a client)
@job_router.get("/job/{job_id}/status")
async def get_job(job_id: UUID) -> JobStatus:
    job = _job_queue.get_job_by_id(job_id)
    return JobStatus(state=job.state, progress=job.percentage_done)


# returns the state of a job (for a client)
@job_router.get("/job/{job_id}/result")
async def get_job(job_id: UUID) -> JobResult:
    job = _job_queue.get_job_by_id(job_id)

    if job.state != "DONE":
        raise HTTPException(status_code=404, detail="Job not done yet")
    return JobResult(
        computation_time=job.computation_time,
        alignments=[
            JobResultCombination(
                combination=combination,
                alignments=alignments,
            )
            for combination, alignments in job.completed_sequences.items()
        ]
    )


@job_router.delete("/job/{job_id}")
async def delete_job(job_id: UUID):
    """
    This is only intended for testing purposes.<br>
    Job deletion might have unwanted side effects, as workers might still be working on the job and work packages are
    not cleaned up.
    """
    logger.info(f"Deleting job")
    if not SETTINGS.enable_job_deletion:
        raise HTTPException(status_code=403, detail="Job deletion is disabled")

    _job_queue.delete_job_by_id(job_id)
