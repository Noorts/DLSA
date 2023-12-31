import logging
from uuid import UUID

from fastapi import APIRouter, HTTPException

from master.api_models import WorkerResources, WorkerId, WorkPackage, WorkResult, RawWorkPackage
from master.job_queue.job_queue import JobQueue
from master.work_package.work_package_collector import WorkPackageCollector
from master.worker.worker_collector import WorkerCollector

worker_router = APIRouter(tags=["worker"])

logger = logging.getLogger(__name__)
_worker_collector = WorkerCollector()
_work_collector = WorkPackageCollector()
_job_queue = JobQueue()


# register a worker, returns a worker id (for worker)
@worker_router.post("/worker/register")
async def register_worker(resources: WorkerResources) -> WorkerId:
    """
    ## Worker registration process
    1. worker registers itself (Provides available resources. Is assigned a worker_id.)
    2. worker requests work (using worker_id) -> no work
    3. sends life pulse, so the master knows that it is still available
    4. worker requests work (using worker_id) -> work available
    5. worker sends work status to master
    6. sends life pulse, so the master knows that it is still available
    7. worker sends work-result to master
    8. worker exits
    9. master notices that the worker is gone (no update for n seconds)...
    """
    worker_id = _worker_collector.register(resources)
    return WorkerId(id=worker_id)


# called in an interval no matter the state
@worker_router.post("/worker/pulse")
async def worker_pulse(worker_id: WorkerId) -> None:
    _worker_collector.add_life_pulse(worker_id.id)


# request work returns a piece of work (for worker, called in an interval while not working)
@worker_router.post("/work/")
async def get_work_for_worker(worker_id: WorkerId) -> WorkPackage | None:
    _worker_collector.add_life_pulse(worker_id.id)
    package = _work_collector.get_new_work_package(worker_id)
    return package


# request work returns a piece of work (for worker, called in an interval while not working)
@worker_router.post("/work/raw")
async def get_raw_work_for_worker(worker_id: WorkerId) -> RawWorkPackage | None:
    _worker_collector.add_life_pulse(worker_id.id)
    package = _work_collector.get_new_raw_work_package(worker_id)
    if not package:
        return None
    return package[0]


@worker_router.get("/work/{work_id}/sequence/{sequence_id}/{worker_id}")
async def get_sequence_for_work(work_id: UUID, sequence_id: UUID, worker_id: UUID) -> str:
    _worker_collector.add_life_pulse(worker_id)
    work_package = _work_collector.get_package_by_id(work_id)
    if sequence_id not in work_package.package.sequences:
        raise HTTPException(status_code=404, detail="Sequence not found")
    return work_package.package.sequences[sequence_id]


# if a worker is done, it sends its results using this endpoint, can be multiple times for one work_id
# to allow incremental result sharing
@worker_router.post("/work/{work_id}/result")
async def work_result(result: WorkResult, work_id: UUID) -> None:
    work_package = _work_collector.get_package_by_id(work_id)
    _worker_collector.add_life_pulse(work_package.worker.worker_id)
    _work_collector.update_work_result(work_id, result)
