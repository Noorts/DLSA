from dataclasses import dataclass

from ..models import WorkerIdType, WorkerResources, WorkerStatus


@dataclass
class Worker:
    worker_id: WorkerIdType
    resources: WorkerResources
    last_seen_alive: int
    status: WorkerStatus
