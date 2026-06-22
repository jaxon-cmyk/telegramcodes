from fastapi.testclient import TestClient

from app.main import app


def _admin_headers(client: TestClient) -> dict[str, str]:
    login = client.post("/auth/login", json={"email": "admin@example.com", "password": "ChangeMe123!"})
    assert login.status_code == 200
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_demo_telegram_sync_search_and_parse_flow():
    with TestClient(app) as client:
        headers = _admin_headers(client)

        connect = client.post(
            "/telegram/connect",
            json={"api_id": "demo", "api_hash": "demo", "phone": "+15555550123"},
            headers=headers,
        )
        assert connect.status_code == 200
        session_id = connect.json()["session_id"]

        verify = client.post(
            "/telegram/verify",
            json={"session_id": session_id, "code": "00000"},
            headers=headers,
        )
        assert verify.status_code == 200
        assert verify.json()["status"] == "connected"

        dialogs = client.get("/telegram/dialogs", headers=headers)
        assert dialogs.status_code == 200
        dialog_id = dialogs.json()[0]["dialog_id"]

        enable = client.post(f"/telegram/channels/{dialog_id}/enable", json={"enabled": True}, headers=headers)
        assert enable.status_code == 200
        assert enable.json()["is_enabled"] is True

        messages = client.get(f"/telegram/messages/{dialog_id}", headers=headers)
        assert messages.status_code == 200
        assert any("EURUSD" in item["text"] for item in messages.json())

        search = client.post("/telegram/search", json={"query": "EURUSD"}, headers=headers)
        assert search.status_code == 200
        assert search.json()

        signals = client.get("/signals", headers=headers)
        assert signals.status_code == 200
        assert any(item["symbol"] == "EURUSD" and item["status"] == "parsed" for item in signals.json())
