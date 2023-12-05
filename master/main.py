import logging

from fastapi import FastAPI

from master.routers import worker_router, job_router

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="DLSA Master")
app.include_router(job_router)
app.include_router(worker_router)
