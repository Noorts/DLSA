from time import sleep

from fastapi.testclient import TestClient

from master.api_models import WorkerId, WorkerResources, WorkPackage
from master.main import app
from master.routers.test_job import JSON_JOB_REQUEST
from master.settings import SETTINGS
from master.utils.interval import set_interval

client = TestClient(app)


def test_register_worker():
    response = client.post(
        "/worker/register", json=WorkerResources(ram_mb=100, cpu_resources=1, gpu_resources=0).model_dump(mode="json")
    )
    assert response.status_code == 200
    worker_id = WorkerId(**response.json())

    # Send a pulse to the master
    response = client.post("/worker/pulse", json=worker_id.model_dump(mode="json"))
    assert response.status_code == 200

    sleep(SETTINGS.worker_cleaning_interval * 2)

    # Send a pulse to the master -> worker should be gone
    response = client.post("/worker/pulse", json=worker_id.model_dump(mode="json"))
    assert response.status_code == 404


def test_get_work_for_worker():
    response = client.post(
        "/worker/register", json=WorkerResources(ram_mb=100, cpu_resources=1, gpu_resources=0).model_dump(mode="json")
    )
    assert response.status_code == 200
    worker_id = WorkerId(**response.json())

    # Send a pulse to the master over and over again
    interval = set_interval(
        lambda: client.post("/worker/pulse", json=worker_id.model_dump(mode="json")), SETTINGS.worker_timout // 2
    )

    # Create a job to consume
    client.post("/job/format/json", json=JSON_JOB_REQUEST)

    # Request work from the master
    response = client.post("/work/", json=worker_id.model_dump(mode="json"))
    assert response.status_code == 200
    json_response = response.json()
    assert json_response
    work_package = WorkPackage(**json_response)
    assert work_package

    interval.stop()
