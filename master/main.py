import logging

from fastapi import FastAPI

from master.routers import worker_router, job_router
from master.trace_time import TraceTimeMiddleware

logging.basicConfig(level=logging.INFO)
uvicorn_access = logging.getLogger("uvicorn.access")
uvicorn_access.disabled = True

app = FastAPI(title="DLSA Master")
app.add_middleware(TraceTimeMiddleware)
app.include_router(job_router)
app.include_router(worker_router)
