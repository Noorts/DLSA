from time import sleep

from fastapi.testclient import TestClient

from master.api_models import WorkerId, WorkerResources, WorkPackage, JobId
from master.settings import SETTINGS
from master.utils.interval import StoppableThread


def test_register_worker(f_client: TestClient):
    response = f_client.post(
        "/worker/register", json=WorkerResources(ram_mb=100, cpu_resources=1, gpu_resources=0).model_dump(mode="json")
    )
    assert response.status_code == 200
    worker_id = WorkerId(**response.json())

    # Send a pulse to the master
    response = f_client.post("/worker/pulse", json=worker_id.model_dump(mode="json"))
    assert response.status_code == 200

    sleep(SETTINGS.worker_cleaning_interval * 2)

    # Send a pulse to the master -> worker should be gone
    response = f_client.post("/worker/pulse", json=worker_id.model_dump(mode="json"))
    assert response.status_code == 404


def test_get_work_for_worker(f_client: TestClient, f_job: JobId, f_worker_node: tuple[WorkerId, StoppableThread]):
    # Request work from the master
    response = f_client.post("/work/", json=f_worker_node[0].model_dump(mode="json"))
    assert response.status_code == 200
    json_response = response.json()
    assert json_response
    work_package = WorkPackage(**json_response)
    assert work_package


def test_work_package_gets_returned(
    f_client: TestClient, f_job: JobId, f_worker_node: tuple[WorkerId, StoppableThread], f_work_package: WorkPackage
):
    # Check if there is work available -> should be none
    response = f_client.post("/work/", json=f_worker_node[0].model_dump(mode="json"))
    assert response.status_code == 200
    assert not response.json()

    # Stop the worker
    f_worker_node[1].stop()

    # Wait for the worker to be removed from the worker list
    sleep(SETTINGS.worker_cleaning_interval * 2)

    # Check if there is work available -> there should be work available again, however we first need to register the
    # worker again

    # Register the worker again
    response = f_client.post(
        "/worker/register", json=WorkerResources(ram_mb=100, cpu_resources=1, gpu_resources=0).model_dump(mode="json")
    )

    # Request work from the master
    response = f_client.post("/work/", json=response.json())
    assert response.status_code == 200
    json_response = response.json()
    assert json_response
    work_package = WorkPackage(**json_response)
    assert work_package
