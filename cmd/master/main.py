import uvicorn
from fastapi import FastAPI

from cmd.master.core.routers import worker_router, job_router

app = FastAPI()
app.include_router(job_router)
app.include_router(worker_router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
