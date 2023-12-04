from typing import Literal
from uuid import UUID

from pydantic import BaseModel

WorkerStatus = Literal["IDLE", "WORKING", "DEAD"]
BenchmarkResult = int


class WorkerId(BaseModel):
    id: UUID


class WorkerResources(BaseModel):
    ram_mb: int
    # determined using benchmarking/cpu_cores, ...
    cpu_resources: int
    # determined using benchmarking/gpu_cores, ...
    gpu_resources: int
    # determined using benchmarking of the actual workload...
    benchmark_result: BenchmarkResult
