from dataclasses import dataclass
from typing import List, Dict

from ..models import JobRequest, TargetQueryCombination


@dataclass
class CompletedSequence:
    target: TargetQueryCombination
    alignment: str
    length: int
    score: int


@dataclass
class QueuedJob:
    request: JobRequest
    completed_sequences: Dict[TargetQueryCombination, CompletedSequence]

    def done(self) -> bool:
        return len(self.completed_sequences) == len(self.request.sequences)

    def missing_sequences(self) -> List[TargetQueryCombination]:
        missing: List[TargetQueryCombination] = []
        for sequence in self.request.sequences:
            if not self.completed_sequences.get(sequence):
                missing.append(sequence)

        return missing
