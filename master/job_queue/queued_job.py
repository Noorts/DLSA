from dataclasses import dataclass
from uuid import UUID

from master.api_models import JobRequest, TargetQueryCombination, JobState, Alignment


@dataclass
class QueuedJob:
    request: JobRequest
    completed_sequences: dict[TargetQueryCombination, list[Alignment]]
    sequences_in_progress: set[TargetQueryCombination]
    id: UUID
    match_score: int
    mismatch_penalty: int
    gap_penalty: int

    @property
    def state(self) -> JobState:
        if self.done():
            return "DONE"
        elif len(self.completed_sequences):
            return "IN_PROGRESS"
        else:
            return "IN_QUEUE"

    @property
    def percentage_done(self) -> float:
        return len(self.completed_sequences) / len(self.request.queries)

    def done(self) -> bool:
        return len(self.completed_sequences) == len(self.request.queries)

    def missing_sequences(self) -> set[TargetQueryCombination]:
        completed_set = set(self.completed_sequences)
        in_progress_set = set(self.sequences_in_progress)

        missing = self.request.queries - (completed_set | in_progress_set)

        return missing
