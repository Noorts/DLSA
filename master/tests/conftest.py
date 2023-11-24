import pytest
from fastapi.testclient import TestClient

from master.api_models import JobId, WorkerResources, WorkerId, WorkPackage
from master.main import app
from master.settings import SETTINGS
from master.tests.test_job import JSON_JOB_REQUEST
from master.utils.interval import set_interval, StoppableThread


@pytest.fixture(scope="module")
def f_job(f_client: TestClient) -> JobId:
    # Create a job to consume
    response = f_client.post("/job/format/json", json=JSON_JOB_REQUEST)
    yield
    job_id = JobId(**response.json())

    # Delete the job
    f_client.delete(f"/job/{job_id.id}")


@pytest.fixture(scope="module")
def f_client() -> TestClient:
    client = TestClient(app)
    yield client
    client.close()


@pytest.fixture(scope="module")
def f_worker_node(f_client: TestClient) -> tuple[WorkerId, StoppableThread]:
    response = f_client.post(
        "/worker/register", json=WorkerResources(ram_mb=100, cpu_resources=1, gpu_resources=0).model_dump(mode="json")
    )
    assert response.status_code == 200
    worker_id = WorkerId(**response.json())

    # Send a pulse to the master over and over again
    interval = set_interval(
        lambda: f_client.post("/worker/pulse", json=worker_id.model_dump(mode="json")),
        SETTINGS.worker_timout // 2,
    )

    yield worker_id, interval
    interval.stop()


@pytest.fixture(scope="module")
def f_work_package(f_client: TestClient, f_job: JobId, f_worker_node: tuple[WorkerId, StoppableThread]) -> WorkPackage:
    response = f_client.post("/work/", json=f_worker_node[0].model_dump(mode="json"))
    assert response.status_code == 200
    json_response = response.json()
    assert json_response
    work_package = WorkPackage(**json_response)
    assert work_package
    yield work_package
