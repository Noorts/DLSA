from typing import Literal
from uuid import UUID

from pydantic import BaseModel

WorkerStatus = Literal["IDLE", "WORKING", "DEAD"]
BenchmarkResult = int


class WorkerId(BaseModel):
    id: UUID


class WorkerResources(BaseModel):
    # determined using benchmarking of the actual workload...
    benchmark_result: BenchmarkResult
