import logging

from master.worker.worker import Worker
from .scheduled_work_package import ScheduledWorkPackage
from .utils import work_packages_from_queries
from .work_scheduler import WorkPackageScheduler

logger = logging.getLogger(__name__)


class PrimitiveWorkPackageScheduler(WorkPackageScheduler):
    def schedule_work_for(self, worker: Worker) -> None | ScheduledWorkPackage:
        unfinished_jobs = self._job_queue.jobs_with_unassigned_sequences()
        if not unfinished_jobs:
            return None
        job = unfinished_jobs.pop(0)
        queries = job.missing_sequences()
        return work_packages_from_queries(job, queries, worker)
