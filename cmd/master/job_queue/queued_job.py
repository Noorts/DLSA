from dataclasses import dataclass
from uuid import UUID

from ..api_models import JobRequest, TargetQueryCombination, JobState, Alignment


@dataclass
class QueuedJob:
    request: JobRequest
    completed_sequences: dict[TargetQueryCombination, Alignment]
    sequences_in_progress: list[TargetQueryCombination]
    id: UUID

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
        return len(self.completed_sequences) / len(self.request.sequences) * 100

    def done(self) -> bool:
        return len(self.completed_sequences) == len(self.request.sequences)

    def missing_sequences(self) -> list[TargetQueryCombination]:
        missing: list[TargetQueryCombination] = []
        for sequence in self.request.sequences:
            if not self.completed_sequences.get(sequence):
                missing.append(sequence)

        return missing
