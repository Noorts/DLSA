import uvicorn
from fastapi import FastAPI

from master.routers import worker_router, job_router

app = FastAPI(title="DLSA Master")
app.include_router(job_router)
app.include_router(worker_router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)