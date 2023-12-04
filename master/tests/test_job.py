from fastapi.testclient import TestClient

from master.api_models import JobId, JobStatus
from master.main import app
from master.tests.data import JOB_REQUEST

client = TestClient(app)


def test_json_endpoint():
    response = client.post(
        "/job/format/json",
        json=JOB_REQUEST.model_dump(mode="json"),
    )

    assert response.status_code == 200
    job_id = JobId(**response.json())

    response = client.get(f"/job/{job_id.id}/status")
    assert JobStatus(**response.json()).state == "IN_QUEUE"
    assert response.status_code == 200

    response = client.get(f"/job/{job_id.id}/result")
    assert response.status_code == 404

    response = client.delete(f"/job/{job_id.id}")
    assert response.status_code == 200
