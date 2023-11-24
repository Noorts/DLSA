from uuid import UUID

from fastapi.testclient import TestClient

from master.api_models import JobRequest, JobId
from master.main import app

client = TestClient(app)

JOB_REQUEST = JobRequest(
    queries={
        UUID("0e22cdce-68b5-4f94-a8a0-2980cbeeb74c"): "ABCD",
        UUID("1e22cdce-68b5-4f94-a8a0-2980cbeeb74c"): "ABCD",
        UUID("2e22cdce-68b5-4f94-a8a0-2980cbeeb74c"): "ABCD",
        UUID("3e22cdce-68b5-4f94-a8a0-2980cbeeb74c"): "ABCD",
        UUID("4e22cdce-68b5-4f94-a8a0-2980cbeeb74c"): "ABCD",
    },
    targets={
        UUID("5e22cdce-68b5-4f94-a8a0-2980cbeeb74c"): "ABCD",
        UUID("6e22cdce-68b5-4f94-a8a0-2980cbeeb74c"): "ABCD",
        UUID("7e22cdce-68b5-4f94-a8a0-2980cbeeb74c"): "ABCD",
        UUID("8e22cdce-68b5-4f94-a8a0-2980cbeeb74c"): "ABCD",
        UUID("9e22cdce-68b5-4f94-a8a0-2980cbeeb74c"): "ABCD",
    },
    sequences=[
        (UUID("0e22cdce-68b5-4f94-a8a0-2980cbeeb74c"), UUID("1e22cdce-68b5-4f94-a8a0-2980cbeeb74c")),
        (UUID("0e22cdce-68b5-4f94-a8a0-2980cbeeb74c"), UUID("2e22cdce-68b5-4f94-a8a0-2980cbeeb74c")),
        (UUID("2e22cdce-68b5-4f94-a8a0-2980cbeeb74c"), UUID("3e22cdce-68b5-4f94-a8a0-2980cbeeb74c")),
    ],
)

JSON_JOB_REQUEST = JOB_REQUEST.model_dump(mode="json")


def test_queue_job():
    response = client.post(
        "/job/format/json",
        json=JSON_JOB_REQUEST,
    )

    assert response.status_code == 200
    job_id = JobId(**response.json())

    response = client.get(f"/job/{job_id.id}/status")
    assert response.status_code == 200

    response = client.get(f"/job/{job_id.id}/result")
    assert response.status_code == 404

    response = client.delete(f"/job/{job_id.id}")
    assert response.status_code == 200
