from uuid import UUID

from pydantic import BaseModel

from .job import TargetQueryCombination, SequenceId, Sequence


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


class WorkAlignment(BaseModel):
    query_alignment: str
    target_alignment: str
    length: int
    score: int
    maxX: int
    maxY: int


class WorkResultCombination(BaseModel):
    combination: TargetQueryCombination
    alignment: WorkAlignment


class WorkResult(BaseModel):
    alignments: list[WorkResultCombination]
