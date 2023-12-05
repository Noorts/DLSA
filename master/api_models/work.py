from uuid import UUID

from pydantic import BaseModel

from .job import TargetQueryCombination, SequenceId, Sequence, Alignment


class RawWorkPackage(BaseModel):
    # work package id
    id: UUID
    job_id: UUID
    queries: list[TargetQueryCombination]
    match_score: int
    mismatch_penalty: int
    gap_penalty: int


class WorkPackage(RawWorkPackage, BaseModel):
    sequences: dict[SequenceId, Sequence]


class WorkStatus(BaseModel):
    percentage_done: float


class WorkResultCombination(BaseModel):
    combination: TargetQueryCombination
    alignment: Alignment


class WorkResult(BaseModel):
    alignments: list[WorkResultCombination]
