from time import sleep
from uuid import UUID

from fastapi.testclient import TestClient

from master.api_models import WorkerId, WorkerResources, WorkPackage, JobId, JobResult, TargetQueryCombination
from master.settings import SETTINGS
from master.tests.data import (
    WORK_RESULT_COMPLETE,
    WORK_RESULT_PART_1,
    WORK_RESULT_PART_2,
    JOB_RESULT_COMPLETE_WITH_DIFFERENT_ALIGNMENT,
    WORK_RESULT_PART_2_DIFFERENT_ALIGNMENT,
    JOB_RESULT_COMPLETE,
)
from master.utils.interval import StoppableThread


def test_register_worker(f_client: TestClient):
    response = f_client.post(
        "/worker/register",
        json=WorkerResources(ram_mb=100, cpu_resources=1, gpu_resources=0, benchmark_result=100).model_dump(
            mode="json"
        ),
    )
    assert response.status_code == 200
    worker_id = WorkerId(**response.json())

    # Send a pulse to the master
    response = f_client.post("/worker/pulse", json=worker_id.model_dump(mode="json"))
    assert response.status_code == 200

    sleep(SETTINGS.worker_cleaning_interval * 3)

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
    assert work_package == WorkPackage(
        id=work_package.id,
        job_id=f_job.id,
        queries=[
            TargetQueryCombination(
                target=UUID("0e22cdce-68b5-4f94-a8a0-2980cbeeb74c"), query=UUID("1e22cdce-68b5-4f94-a8a0-2980cbeeb74c")
            ),
            TargetQueryCombination(
                target=UUID("0e22cdce-68b5-4f94-a8a0-2980cbeeb74c"), query=UUID("2e22cdce-68b5-4f94-a8a0-2980cbeeb74c")
            ),
            TargetQueryCombination(
                target=UUID("2e22cdce-68b5-4f94-a8a0-2980cbeeb74c"), query=UUID("3e22cdce-68b5-4f94-a8a0-2980cbeeb74c")
            ),
        ],
        sequences={
            UUID("0e22cdce-68b5-4f94-a8a0-2980cbeeb74c"): "ABCD",
            UUID("2e22cdce-68b5-4f94-a8a0-2980cbeeb74c"): "ABCD",
            UUID("3e22cdce-68b5-4f94-a8a0-2980cbeeb74c"): "ABCD",
            UUID("1e22cdce-68b5-4f94-a8a0-2980cbeeb74c"): "ABCD",
        },
        match_score=1,
        mismatch_penalty=-1,
        gap_penalty=-1,
    )


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
    sleep(SETTINGS.worker_cleaning_interval * 2 + SETTINGS.work_package_cleaning_interval * 2)

    # Check if there is work available -> there should be work available again
    # However, we first need to register the worker again
    response = f_client.post(
        "/worker/register",
        json=WorkerResources(ram_mb=100, cpu_resources=1, gpu_resources=0, benchmark_result=100).model_dump(
            mode="json"
        ),
    )

    # Request work from the master
    response = f_client.post("/work/", json=response.json())
    assert response.status_code == 200
    json_response = response.json()
    assert json_response
    work_package = WorkPackage(**json_response)
    assert work_package


def test_work_package_returned_successfully_and_completely(
    f_client: TestClient, f_job: JobId, f_worker_node: tuple[WorkerId, StoppableThread], f_work_package: WorkPackage
):
    # Return some arbitrary result
    response = f_client.post(f"/work/{f_work_package.id}/result", json=WORK_RESULT_COMPLETE.model_dump(mode="json"))
    assert response.status_code == 200

    # Check if there is work available -> should be none
    response = f_client.post("/work/", json=f_worker_node[0].model_dump(mode="json"))
    assert response.status_code == 200
    assert not response.json()

    # Get the job result
    response = f_client.get(f"/job/{f_job.id}/result")
    assert response.status_code == 200
    assert JobResult(**response.json())


def test_work_two_different_alignments_for_work_package_returned(
    f_client: TestClient, f_job: JobId, f_worker_node: tuple[WorkerId, StoppableThread], f_work_package: WorkPackage
):
    response = f_client.post(f"/work/{f_work_package.id}/result", json=WORK_RESULT_PART_1.model_dump(mode="json"))
    assert response.status_code == 200
    response = f_client.post(f"/work/{f_work_package.id}/result", json=WORK_RESULT_PART_2.model_dump(mode="json"))
    assert response.status_code == 200

    # Send the second part again, but this time with a different score and alignment
    response = f_client.post(
        f"/work/{f_work_package.id}/result", json=WORK_RESULT_PART_2_DIFFERENT_ALIGNMENT.model_dump(mode="json")
    )
    assert response.status_code == 200

    # Get the job result
    response = f_client.get(f"/job/{f_job.id}/result")
    assert response.status_code == 200

    # Check if the result is correct
    job_result = JobResult(**response.json())
    assert job_result.alignments == JOB_RESULT_COMPLETE_WITH_DIFFERENT_ALIGNMENT.alignments


def test_work_package_partially_returned_and_picked_up_by_other_worker(
    f_client: TestClient, f_job: JobId, f_worker_node: tuple[WorkerId, StoppableThread], f_work_package: WorkPackage
):
    # Return a partial result
    response = f_client.post(f"/work/{f_work_package.id}/result", json=WORK_RESULT_PART_1.model_dump(mode="json"))
    print(WORK_RESULT_PART_1.model_dump(mode="json"))
    assert response.status_code == 200

    # Check that there is no work available
    response = f_client.post("/work/", json=f_worker_node[0].model_dump(mode="json"))
    assert response.status_code == 200
    assert not response.json()

    # Close the worker
    f_worker_node[1].stop()

    # Wait for the worker to be removed from the worker list
    sleep(SETTINGS.worker_cleaning_interval * 2.5 + SETTINGS.work_package_cleaning_interval * 2.5)

    # Register a new worker
    response = f_client.post(
        "/worker/register",
        json=WorkerResources(ram_mb=100, cpu_resources=1, gpu_resources=0, benchmark_result=100).model_dump(
            mode="json"
        ),
    )
    assert response.status_code == 200

    # Request work from the master
    response = f_client.post("/work/", json=response.json())
    assert response.status_code == 200
    new_work_package = WorkPackage(**response.json())

    # Return the rest of the result
    response = f_client.post(f"/work/{new_work_package.id}/result", json=WORK_RESULT_PART_2.model_dump(mode="json"))
    assert response.status_code == 200

    # Get the job result
    response = f_client.get(f"/job/{f_job.id}/result")
    assert response.status_code == 200

    # Check if the result is correct
    job_result = JobResult(**response.json())
    assert job_result.alignments == JOB_RESULT_COMPLETE.alignments
