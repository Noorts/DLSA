from __future__ import annotations
import json
from typing import Literal, Annotated
from uuid import UUID

from fastapi import HTTPException
from pydantic import BaseModel, model_validator
from pydantic import Field

Sequence = str
SequenceId = UUID
JobState = Literal["IN_QUEUE", "IN_PROGRESS", "DONE"]


class TargetQueryCombination(BaseModel):
    target: SequenceId
    query: SequenceId

    def __hash__(self):
        return hash((self.target, self.query))


# noinspection PyNestedDecorators
class MultipartJobRequest(BaseModel):
    queries: list[TargetQueryCombination]
    match_score: int
    mismatch_penalty: int
    gap_penalty: int

    @model_validator(mode="before")
    @classmethod
    def validate_to_json(cls, value):
        if isinstance(value, str):
            return cls(**json.loads(value))
        return value


# noinspection PyNestedDecorators
class JobRequest(MultipartJobRequest, BaseModel):
    sequences: dict[SequenceId, Sequence]

    def assert_required_sequences(self) -> JobRequest:
        for combi in self.queries:
            if combi.target not in self.sequences:
                raise HTTPException(400, f"Missing sequence for target {combi.target}")
            if combi.query not in self.sequences:
                raise HTTPException(400, f"Missing sequence for query {combi.query}")

        return self


class JobId(BaseModel):
    id: UUID


class JobStatus(BaseModel):
    state: JobState
    # the progress as percentage [0-1]
    progress: Annotated[float, Field(strict=True, ge=0, le=1)]


class Alignment(BaseModel):
    # ABDAABDABDAC
    alignment: str
    length: int
    score: int


class JobResultCombination(BaseModel):
    combination: TargetQueryCombination
    alignments: list[Alignment]


# the result returned to the client, ordered by length
class JobResult(BaseModel):
    alignments: list[JobResultCombination]
