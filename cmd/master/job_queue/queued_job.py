from dataclasses import dataclass

from ..api_models import JobRequest, TargetQueryCombination, JobState


@dataclass
class CompletedSequence:
    target: TargetQueryCombination
    alignment: str
    length: int
    score: int


@dataclass
class QueuedJob:
    request: JobRequest
    completed_sequences: dict[TargetQueryCombination, CompletedSequence]

    @property
    def id(self) -> str:
        return self.request.id

    @property
    def state(self) -> JobState:
        if self.done():
            return "DONE"
        elif len(self.completed_sequences):
            return "IN_PROGRESS"
        else:
            return "IN_QUEUE"

    def done(self) -> bool:
        return len(self.completed_sequences) == len(self.request.sequences)

    def missing_sequences(self) -> list[TargetQueryCombination]:
        missing: list[TargetQueryCombination] = []
        for sequence in self.request.sequences:
            if not self.completed_sequences.get(sequence):
                missing.append(sequence)

        return missing

    def completed_percentage(self) -> float:
        return len(self.completed_sequences) / len(self.request.sequences)
