from dataclasses import dataclass
from uuid import UUID

from master.api_models import TargetQueryCombination, Sequence, SequenceId
from master.job_queue.queued_job import QueuedJob
from master.worker.worker import Worker


@dataclass
class InternalWorkPackage:
    # work package id
    id: UUID
    job: QueuedJob
    sequences: dict[SequenceId, Sequence]
    queries: list[TargetQueryCombination]
    match_score: int
    mismatch_penalty: int
    gap_penalty: int


@dataclass
class ScheduledWorkPackage:
    package: InternalWorkPackage
    worker: Worker

    @property
    def percentage_done(self) -> float:
        # Get the length of the sequences that should be done in the work package
        sequence_length = len(self.package.queries)
        completed_sequences = 0

        for sequence in self.package.queries:
            if sequence in self.package.job.completed_sequences:
                completed_sequences += 1

        return completed_sequences / sequence_length
