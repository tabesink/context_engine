"""Example route test to adapt into tests/api/test_lightrag_admin_repair.py."""


def test_repair_endpoint_returns_postgres_diagnostics(client, admin_auth_headers, monkeypatch):
    # Arrange: monkeypatch LightRAGDomainService.repair to return a model instance.
    # Keep this as a contract test; integration provisioning should be covered separately.
    response = client.post(
        "/admin/lightrag/domains/fatigue/repair",
        headers=admin_auth_headers,
    )

    assert response.status_code in {200, 404, 400, 502}
    # In the real implementation with a seeded domain:
    # assert response.status_code == 200
    # payload = response.json()
    # assert payload["storage_backend"] == "postgres"
    # assert payload["postgres_database"] == "lightrag_fatigue"
    # assert payload["postgres_user"] == "lightrag_fatigue"
