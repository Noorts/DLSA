from uuid import uuid4, UUID

from .work_scheduler import WorkScheduler, ScheduledWorkPackage, WorkPackageStatus
from ...api_models import  WorkPackage
from ...utils.singleton import Singleton


class PrimitiveWorkScheduler(WorkScheduler):
    def schedule_work_for(self, worker_id: UUID) -> None | WorkPackage:
        job = self._job_queue.unfinished_jobs().pop()
        if not job:
            return None

        package = WorkPackage(
            id=uuid4(),
            targets=job.request.targets,
            queries=job.request.queries,
            sequences=job.request.sequences,
        )

        worker = self._worker_collector.get_worker_by_id(worker_id)

        self._packages_in_process[package.id] = ScheduledWorkPackage(
            package=package,
            worker=worker,
            status=WorkPackageStatus(percentage_done=0.0),
        )
        return package

    def abort_work_package(self, work_package: UUID):
        del self._packages_in_process[work_package]
