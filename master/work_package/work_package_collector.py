from uuid import UUID

from fastapi import HTTPException

from master.api_models import WorkResult, WorkerId, WorkPackage
from master.settings import SETTINGS
from master.utils.cleaner import Cleaner
from master.utils.singleton import Singleton
from master.worker.worker_collector import WorkerCollector
from ._scheduler.work_scheduler import WorkPackageScheduler, ScheduledWorkPackage


class WorkPackageNotFoundException(HTTPException):
    def __init__(self, work_package_id: UUID):
        super().__init__(status_code=404, detail=f"Work package with id {work_package_id} not found")


class WorkPackageCollector(Cleaner, Singleton):
    def __init__(self):
        self._worker_collector = WorkerCollector()
        self._work_scheduler = WorkPackageScheduler.create()
        self._work_packages: list[ScheduledWorkPackage] = []
        super().__init__(interval=SETTINGS.work_package_cleaning_interval)

    def get_package_by_id(self, work_package_id: UUID) -> ScheduledWorkPackage:
        for package in self._work_packages:
            if package.package.id == work_package_id:
                return package

        raise WorkPackageNotFoundException(work_package_id)

    def update_work_result(self, work_id: UUID, result: WorkResult) -> None:
        work_package = self.get_package_by_id(work_id)
        completed_sequences = work_package.package.job.completed_sequences

        for [target_query_combination, alignment] in result.alignments:
            completed_sequences[target_query_combination] = alignment
            # Remove the sequence from the in progress list
            work_package.package.job.sequences_in_progress.remove(target_query_combination)

    def get_new_work_package(self, worker_id: WorkerId) -> None | WorkPackage:
        worker = self._worker_collector.get_worker_by_id(worker_id.id)
        scheduled_package = self._work_scheduler.schedule_work_for(worker)
        if not scheduled_package:
            return None

        self._work_packages.append(scheduled_package)
        return WorkPackage(
            id=scheduled_package.package.id,
            job_id=scheduled_package.package.job.id,
            sequences=scheduled_package.package.sequences,
        )

    def execute_clean(self) -> None:
        print(self._work_packages)
        for package in self._work_packages:
            if package.worker.status == "DEAD":
                self._work_scheduler.abort_work_package(package)
                self._work_packages.remove(package)
