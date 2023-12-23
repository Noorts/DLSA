from dataclasses import dataclass
from uuid import UUID

from master.api_models import JobRequest, TargetQueryCombination, JobState, Alignment
from master.utils.log_time import log_time
from master.utils.try_until_succeeds import try_until_succeeds


@dataclass
class QueuedJob:
    request: JobRequest
    completed_sequences: dict[TargetQueryCombination, list[Alignment]]
    sequences_in_progress: set[TargetQueryCombination]
    id: UUID
    match_score: int
    mismatch_penalty: int
    gap_penalty: int
    start_time: float
    computation_time: float

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

    @log_time
    def missing_sequences(self) -> set[TargetQueryCombination]:
        completed_set = self.completed_sequences.keys()
        in_progress_set = self.sequences_in_progress

        missing = try_until_succeeds(lambda: self.request.queries - (completed_set | in_progress_set))

        return missing
