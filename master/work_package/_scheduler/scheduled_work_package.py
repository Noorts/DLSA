from dataclasses import dataclass
from uuid import UUID

from master.api_models import TargetQueryCombination, Sequence, SequenceId
from master.job_queue.queued_job import QueuedJob
from master.utils.log_time import log_time
from master.utils.time import current_ms
from master.utils.try_until_succeeds import try_until_succeeds
from master.worker.worker import Worker


@dataclass
class InternalWorkPackage:
    # work package id
    id: UUID
    job: QueuedJob
    sequences: dict[SequenceId, Sequence]
    queries: set[TargetQueryCombination]
    match_score: int
    mismatch_penalty: int
    gap_penalty: int


@dataclass
class ScheduledWorkPackage:
    package: InternalWorkPackage
    worker: Worker
    start_time: int
    expected_ms: int

    @property
    @log_time
    def percentage_done(self) -> float:
        # Get the length of the sequences that should be done in the work package
        sequence_length = len(self.package.queries)
        completed_sequences_set = self.package.job.completed_sequences.keys()
        completed_sequences = try_until_succeeds(lambda: len(self.package.queries & completed_sequences_set))
        return completed_sequences / sequence_length

    def done(self) -> bool:
        return self.percentage_done == 1

    def is_too_slow(self) -> bool:
        # return True if worker is 60 seconds slower than 10x as slow as expected
        return self.start_time + self.percentage_done * self.expected_ms * 10 + 60000 < current_ms()
