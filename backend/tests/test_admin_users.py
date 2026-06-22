from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


def _admin_headers(client: TestClient) -> dict[str, str]:
    login = client.post("/auth/login", json={"email": "admin@example.com", "password": "ChangeMe123!"})
    assert login.status_code == 200
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_admin_can_create_user_and_reset_password():
    with TestClient(app) as client:
        headers = _admin_headers(client)
        email = f"created-user-{uuid4().hex}@example.com"

        created = client.post(
            "/admin/users",
            json={"email": email, "password": "StartPass123!", "role": "user", "is_active": True},
            headers=headers,
        )
        assert created.status_code in {200, 400}
        if created.status_code == 400:
            users = client.get("/admin/users", headers=headers).json()
            user_id = next(item["id"] for item in users if item["email"] == email)
        else:
            user_id = created.json()["id"]

        login = client.post("/auth/login", json={"email": email, "password": "StartPass123!"})
        assert login.status_code == 200

        reset = client.patch(
            f"/admin/users/{user_id}",
            json={"password": "NewPass123!"},
            headers=headers,
        )
        assert reset.status_code == 200

        old_login = client.post("/auth/login", json={"email": email, "password": "StartPass123!"})
        assert old_login.status_code == 401
        new_login = client.post("/auth/login", json={"email": email, "password": "NewPass123!"})
        assert new_login.status_code == 200
