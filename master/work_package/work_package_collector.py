import logging
from typing import Tuple
from uuid import UUID

from fastapi import HTTPException

from master.api_models import WorkResult, WorkerId, WorkPackage, RawWorkPackage
from master.settings import SETTINGS
from master.utils.cleaner import Cleaner
from master.utils.singleton import Singleton
from master.worker.worker_collector import WorkerCollector
from ._scheduler.work_scheduler import WorkPackageScheduler, ScheduledWorkPackage

logger = logging.getLogger(__name__)


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

        for res in result.alignments:
            if res.combination not in completed_sequences:
                completed_sequences[res.combination] = []

            completed_sequences[res.combination].append(res.alignment)
            # Remove the sequence from the in progress list if it is in there
            if res.combination in work_package.package.job.sequences_in_progress:
                work_package.package.job.sequences_in_progress.remove(res.combination)

        # Check if the work package is done
        if work_package.done():
            logger.info(f"Work package {work_package.package.id} is done")
            work_package.worker.status = "IDLE"

        # See if the job is done
        if work_package.package.job.done():
            logger.info(f"Work package {work_package.package.id} is done")

    def get_new_work_package(self, worker_id: WorkerId) -> None | WorkPackage:
        new = self.get_new_raw_work_package(worker_id)
        if not new:
            return None
        package, scheduled_package = new
        return WorkPackage(
            **package.model_dump(),
            sequences={str(uuid): sequence for uuid, sequence in scheduled_package.package.sequences.items()},
        )

    def get_new_raw_work_package(self, worker_id: WorkerId) -> None | Tuple[RawWorkPackage, ScheduledWorkPackage]:
        worker = self._worker_collector.get_worker_by_id(worker_id.id)
        scheduled_package = self._work_scheduler.schedule_work_for(worker)

        if not scheduled_package:
            return None

        self._work_packages.append(scheduled_package)

        package = RawWorkPackage(
            id=scheduled_package.package.id,
            job_id=scheduled_package.package.job.id,
            queries=[{"target": query.target, "query": query.query} for query in scheduled_package.package.queries],
            match_score=scheduled_package.package.match_score,
            mismatch_penalty=scheduled_package.package.mismatch_penalty,
            gap_penalty=scheduled_package.package.gap_penalty,
        )
        logger.info(f"Created work package {package.id} to worker {worker_id} with {len(package.queries)} queries")
        worker.status = "WORKING"
        return package, scheduled_package

    def execute_clean(self) -> None:
        for package in self._work_packages:
            if package.worker.status == "DEAD":
                logger.info(
                    f"Aborting work package {package.package.id} because worker {package.worker.worker_id} is dead"
                )
                self._work_scheduler.abort_work_package(package)
                self._work_packages.remove(package)
