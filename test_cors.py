from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_localhost_dynamic_port_allowed_for_cors():
    response = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:54250",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:54250"
