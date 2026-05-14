def test_healthz(client):
    r = client.get("/healthz")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert "version" in body


def test_unauthorized_endpoints(client):
    assert client.get("/api/v1/due-diligence/jobs/ddj_x").status_code == 401
    assert client.get("/api/v1/certificates/cert_x").status_code == 401
