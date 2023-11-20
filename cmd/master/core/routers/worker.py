from fastapi import APIRouter

from ..models import WorkerResources, WorkerId, WorkPackage, WorkStatus, WorkResult
from ..worker.worker_collector import WorkerCollector

worker_router = APIRouter()
_worker_collector = WorkerCollector()


# 1. worker registers itself (Provides available resources. Is assigned a worker_id.)
# 2. worker requests work (using worker_id) -> no work
# 3. sends life pulse, so the master knows that it is still available
# 4. worker requests work (using worker_id) -> work available
# 5. worker sends work status to master
# 6. sends life pulse, so the master knows that it is still available
# 7. worker sends work-result to master
# 8. worker exits
# 9. master notices that the worker is gone (no update for n seconds)...


@worker_router.post("/worker/register")
def register_worker(resources: WorkerResources) -> WorkerId:
    return WorkerId(id=_worker_collector.register(resources))


# called in an interval no matter the state
@worker_router.post("/worker/pulse")
def worker_pulse(worker_id: WorkerId) -> None:
    _worker_collector.add_life_pulse(worker_id.id)


# request work returns a piece of work (for worker, called in an interval while not working)
@worker_router.post("/work/")
def get_work(worker_id: WorkerId) -> WorkPackage | None:
    pass


# send the status of a current work (how much is done, ...), called in an interval while working
@worker_router.post("/work/{work_id}/status")
def update_work_status(work_status: WorkStatus) -> None:
    pass


# if a worker is done, it sends its results using this endpoint, can be multiple times for one work_id
# to allow incremental result sharing
@worker_router.post("/work/{work_id}/result")
def work_result(result: WorkResult) -> None:
    pass
