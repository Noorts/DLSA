from uuid import UUID

from fastapi import HTTPException

from .scheduler.work_scheduler import WorkPackageScheduler, ScheduledWorkPackage
from ..api_models import WorkPackage
from ..api_models import WorkResult
from ..settings import SETTINGS
from ..utils.cleaner import Cleaner
from ..utils.singleton import Singleton
from ..worker.worker import Worker
from ..worker.worker_collector import WorkerCollector


class WorkPackageNotFoundException(HTTPException):
    def __init__(self, work_package_id: UUID):
        super().__init__(status_code=404, detail=f"Work package with id {work_package_id} not found")


class WorkPackageCollector(Cleaner, Singleton):
    def __init__(self):
        self._worker_collector = WorkerCollector()
        self._work_scheduler = WorkPackageScheduler.create()
        self._work_packages: list[ScheduledWorkPackage] = []
        super().__init__(interval=SETTINGS.work_package_cleaning_interval)

    def get_work(self, worker: Worker) -> WorkPackage | None:
        work = self._work_scheduler.schedule_work_for(worker)
        if not work:
            return None

        self._work_packages += work
        return work.package

    def execute_clean(self) -> None:
        for package in self._work_packages:
            if package.worker.status == "DEAD":
                self._work_scheduler.abort_work_package(package)
                self._work_packages.remove(package)

    def get_package_by_id(self, work_package_id: UUID) -> ScheduledWorkPackage:
        for package in self._work_packages:
            if package.package.id == work_package_id:
                return package

        raise WorkPackageNotFoundException(work_package_id)

    def update_work_result(self, work_id: UUID, result: WorkResult) -> None:
        work_package = self.get_package_by_id(work_id)
        # TODO Job does not exist anymore
        completed_sequences = work_package.package.job.completed_sequences

        for [target_query_combination, alignment] in result.alignments:
            completed_sequences[target_query_combination] = alignment
