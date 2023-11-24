from uuid import uuid4, UUID

from fastapi import HTTPException

from master.api_models import WorkerResources
from master.settings import SETTINGS
from master.utils.cleaner import Cleaner
from master.utils.singleton import Singleton
from master.utils.time import current_sec
from .worker import Worker


class WorkerNotFoundException(HTTPException):
    def __init__(self, worker_id: UUID):
        super().__init__(status_code=404, detail=f"Worker with id {worker_id} not found")


class WorkerCollector(Cleaner, Singleton):
    def __init__(self):
        self._workers: dict[UUID, Worker] = {}
        super().__init__(interval=SETTINGS.worker_cleaning_interval)

    @property
    def workers(self) -> list[Worker]:
        return list(self._workers.values())

    def register(self, resources: WorkerResources) -> UUID:
        worker_id = uuid4()
        self._workers[worker_id] = Worker(
            worker_id=worker_id, resources=resources, last_seen_alive=current_sec(), status="IDLE"
        )
        return worker_id

    def get_worker_by_id(self, worker_id: UUID) -> Worker:
        worker = self._workers.get(worker_id)
        if not worker:
            raise WorkerNotFoundException(worker_id)

        return worker

    def add_life_pulse(self, worker_id: UUID) -> None:
        worker = self.get_worker_by_id(worker_id)
        worker.last_seen_alive = current_sec()

    def idle_workers(self) -> list[Worker]:
        return [worker for worker in self._workers.values() if worker.status == "IDLE"]

    def is_alive(self, worker: Worker | UUID) -> bool:
        if isinstance(worker, UUID):
            try:
                worker = self.get_worker_by_id(worker)
            except WorkerNotFoundException:
                return False
        return worker.last_seen_alive > current_sec() - SETTINGS.worker_timout and worker.status != "DEAD"

    def execute_clean(self) -> None:
        for worker in self._workers.values():
            if not self.is_alive(worker):
                self._workers[worker.worker_id].status = "DEAD"
                del self._workers[worker.worker_id]
