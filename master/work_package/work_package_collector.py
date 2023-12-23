import logging
from typing import Tuple
from uuid import UUID

from fastapi import HTTPException

from master.api_models import WorkResult, WorkerId, WorkPackage, RawWorkPackage, Alignment
from master.settings import SETTINGS
from master.utils.cleaner import Cleaner
from master.utils.singleton import Singleton
from master.utils.verify import verify_result
from master.worker.worker_collector import WorkerCollector
from ._scheduler.work_scheduler import WorkPackageScheduler, ScheduledWorkPackage
from ..utils.log_time import log_time
import time

logger = logging.getLogger(__name__)


class WorkPackageNotFoundException(HTTPException):
    def __init__(self, work_package_id: UUID):
        super().__init__(status_code=404, detail=f"Work package with id {work_package_id} not found")


class WorkPackageCollector(Cleaner, Singleton):
    def __init__(self):
        self._worker_collector = WorkerCollector()
        self._work_scheduler = WorkPackageScheduler.create()
        self._work_packages: list[ScheduledWorkPackage] = []
        self._verify_work = SETTINGS.verify_work
        super().__init__(interval=SETTINGS.work_package_cleaning_interval)

    def get_package_by_id(self, work_package_id: UUID) -> ScheduledWorkPackage:
        for package in self._work_packages:
            if package.package.id == work_package_id:
                return package

        raise WorkPackageNotFoundException(work_package_id)

    def update_work_result(self, work_id: UUID, result: WorkResult) -> None:
        work_package = self.get_package_by_id(work_id)
        completed_sequences = work_package.package.job.completed_sequences

        if self._verify_work and not self._worker_collector.is_alive(work_package.worker):  # malicious deleted worker is marked dead
            return

        for res in result.alignments:
            if self._verify_work and not verify_result(work_package.package, res):
                work_package.package.job.sequences_in_progress.update(work_package.package.job.completed_sequences.keys())
                work_package.package.job.completed_sequences.clear()
                self._worker_collector.remove_worker(work_package.worker)
                return

            if res.combination not in completed_sequences:
                completed_sequences[res.combination] = []

            completed_sequences[res.combination].append(Alignment(
                alignment=res.alignment.query_alignment,
                length=res.alignment.length,
                score=res.alignment.score)
            )
            # Remove the sequence from the in progress list if it is in there
            try:
                work_package.package.job.sequences_in_progress.remove(res.combination)
            except ValueError:
                pass

        # Check if the work package is done
        if work_package.done():
            logger.info(f"Work package {work_package.package.id} is done")
            work_package.worker.status = "IDLE"

        # See if the job is done
        if work_package.package.job.done():
            t = ( time.time() - work_package.package.job.start_time)
            print('computation time: ', t)
            work_package.package.job.computation_time = t
            logger.info(f"Work package {work_package.package.id} is done")

        # Remove worker if it is far slower than expected
        if work_package.is_too_slow():
            self._worker_collector.remove_worker(work_package.worker)

    def get_new_work_package(self, worker_id: WorkerId) -> None | WorkPackage:
        new = self.get_new_raw_work_package(worker_id)
        if not new:
            return None
        package, scheduled_package = new
        return WorkPackage(
            **package.model_dump(),
            sequences={str(uuid): sequence for uuid, sequence in scheduled_package.package.sequences.items()},
        )

    @log_time
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
        logger.info(f"Created work package for worker with {len(package.queries)} queries")
        worker.status = "WORKING"
        return package, scheduled_package

    def execute_clean(self) -> None:
        for package in self._work_packages:
            if package.worker.status == "DEAD":
                logger.info(f"Aborting work package because worker is dead")
                logger.info("Preparing to assign it to a different worker")
                self._work_scheduler.abort_work_package(package)
                self._work_packages.remove(package)
