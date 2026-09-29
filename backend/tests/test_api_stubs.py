"""Basic smoke tests for authentication and a couple of stub API endpoints."""

from fastapi.testclient import TestClient
from jose import jwt

from app.main import app

client = TestClient(app)


def test_submit_query_without_auth_returns_401() -> None:
    response = client.post(
        "/api/v1/queries", json={"query_text": "hello", "session_id": "s1"}
    )

    assert response.status_code == 401


def test_submit_query_with_stub_token_returns_202() -> None:
    token = jwt.encode({"sub": "user-1", "role": "legal_analyst"}, key="secret", algorithm="HS256")

    auth_header = "Bearer " + token
    response = client.post(
        "/api/v1/queries",
        json={"query_text": "hello", "session_id": "s1"},
        headers={"Authorization": auth_header},
    )

    assert response.status_code == 202
    assert response.json()["status"] == "QUEUED"


def test_query_result_reflects_completed_pipeline_output() -> None:
    token = jwt.encode({"sub": "user-1", "role": "legal_analyst"}, key="secret", algorithm="HS256")
    auth_header = "Bearer " + token

    submit_response = client.post(
        "/api/v1/queries",
        json={"query_text": "hello", "session_id": "s1"},
        headers={"Authorization": auth_header},
    )
    query_id = submit_response.json()["query_id"]

    result_response = client.get(
        f"/api/v1/queries/{query_id}/result", headers={"Authorization": auth_header}
    )

    assert result_response.status_code == 200
    body = result_response.json()
    assert body["query_id"] == query_id
    assert body["status"] in {"COMPLETED", "COMPLETED_WITH_WARNINGS"}
    assert body["generated_answer"] is not None


def test_query_result_returns_404_for_unknown_query_id() -> None:
    token = jwt.encode({"sub": "user-1", "role": "legal_analyst"}, key="secret", algorithm="HS256")
    auth_header = "Bearer " + token

    response = client.get(
        "/api/v1/queries/unknown-query-id/result", headers={"Authorization": auth_header}
    )

    assert response.status_code == 404


def test_audit_trail_requires_compliance_role() -> None:
    token = jwt.encode({"sub": "user-1", "role": "legal_analyst"}, key="secret", algorithm="HS256")

    auth_header = "Bearer " + token
    response = client.get(
        "/api/v1/audit/trail", headers={"Authorization": auth_header}
    )

    assert response.status_code == 403


def test_document_upload_status_and_delete_require_auth() -> None:
    response = client.post(
        "/api/v1/documents/upload", files={"file": ("test.txt", b"hello", "text/plain")}
    )
    assert response.status_code == 401

    response = client.get("/api/v1/documents/some-id/status")
    assert response.status_code == 401

    response = client.delete("/api/v1/documents/some-id")
    assert response.status_code == 401


def test_document_upload_status_and_delete_happy_path() -> None:
    token = jwt.encode({"sub": "user-1", "role": "legal_analyst"}, key="secret", algorithm="HS256")
    auth_header = "Bearer " + token

    upload_response = client.post(
        "/api/v1/documents/upload",
        headers={"Authorization": auth_header},
        files={"file": ("test.txt", b"hello world", "text/plain")},
    )
    assert upload_response.status_code == 202
    document_id = upload_response.json()["document_id"]
    assert upload_response.json()["status"] == "PROCESSING"

    status_response = client.get(
        f"/api/v1/documents/{document_id}/status", headers={"Authorization": auth_header}
    )
    assert status_response.status_code == 200
    assert status_response.json()["document_id"] == document_id

    delete_response = client.delete(
        f"/api/v1/documents/{document_id}", headers={"Authorization": auth_header}
    )
    assert delete_response.status_code == 204
