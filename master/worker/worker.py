from dataclasses import dataclass
from uuid import UUID

from master.api_models import WorkerResources, WorkerStatus


@dataclass
class Worker:
    worker_id: UUID
    resources: WorkerResources
    last_seen_alive: int
    status: WorkerStatus
