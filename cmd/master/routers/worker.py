from uuid import UUID

from fastapi import APIRouter

from ..api_models import WorkerResources, WorkerId, WorkPackage, WorkResult
from ..job_queue.job_queue import JobQueue
from ..work_package.scheduler.work_scheduler import WorkPackageScheduler
from ..work_package.work_package_collector import WorkPackageCollector
from ..worker.worker_collector import WorkerCollector

worker_router = APIRouter(tags=["worker"])

_worker_collector = WorkerCollector()
_work_scheduler = WorkPackageScheduler.create()
_work_collector = WorkPackageCollector()
_job_queue = JobQueue()


# register a worker, returns a worker id (for worker)
@worker_router.post("/worker/register")
def register_worker(resources: WorkerResources) -> WorkerId:
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
def worker_pulse(worker_id: WorkerId) -> None:
    _worker_collector.add_life_pulse(worker_id.id)


# request work returns a piece of work (for worker, called in an interval while not working)
@worker_router.post("/work/")
def get_work_for_worker(worker_id: WorkerId) -> WorkPackage | None:
    worker = _worker_collector.get_worker_by_id(worker_id.id)
    scheduled_package = _work_scheduler.schedule_work_for(worker)
    if not scheduled_package:
        return None

    return WorkPackage(
        id=scheduled_package.package.id,
        job_id=scheduled_package.package.job.id,
        sequences=scheduled_package.package.sequences,
    )


# if a worker is done, it sends its results using this endpoint, can be multiple times for one work_id
# to allow incremental result sharing
@worker_router.post("/work/{work_id}/result")
def work_result(result: WorkResult, work_id: UUID) -> None:
    _work_collector.update_work_result(work_id, result)
