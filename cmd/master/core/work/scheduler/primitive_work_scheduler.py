from .work_scheduler import WorkScheduler
from ...models import WorkerIdType
from ...utils.singleton import Singleton


class PrimitiveWorkScheduler(WorkScheduler, Singleton):
    def schedule_work_for(self, worker_id: WorkerIdType):
        raise NotImplementedError()
