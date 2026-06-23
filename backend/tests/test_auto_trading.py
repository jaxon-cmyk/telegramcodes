from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


def _admin_headers(client: TestClient) -> dict[str, str]:
    login = client.post("/auth/login", json={"email": "admin@example.com", "password": "ChangeMe123!"})
    assert login.status_code == 200
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_telegram_sync_auto_executes_when_rule_allows_signal():
    with TestClient(app) as client:
        headers = _admin_headers(client)
        dialog_id = f"auto-trade-{uuid4().hex}"

        connect = client.post(
            "/telegram/connect",
            json={"api_id": "demo", "api_hash": "demo", "phone": "+15555550123"},
            headers=headers,
        )
        assert connect.status_code == 200
        verify = client.post(
            "/telegram/verify",
            json={"session_id": connect.json()["session_id"], "code": "00000"},
            headers=headers,
        )
        assert verify.status_code == 200

        channel = client.post(f"/telegram/channels/{dialog_id}/enable", json={"enabled": True}, headers=headers)
        assert channel.status_code == 200
        channel_id = channel.json()["id"]

        account = client.post(
            "/mt5/accounts/connect",
            json={
                "name": "Demo MT5",
                "provider": "self_hosted_mt5_bridge",
                "provider_account_id": f"demo-{uuid4().hex}",
                "credentials": {"token": "demo"},
            },
            headers=headers,
        )
        assert account.status_code == 200

        rule = client.post(
            "/automation-rules",
            json={
                "name": "Auto EURUSD",
                "channel_id": channel_id,
                "mt5_account_id": account.json()["id"],
                "is_enabled": True,
                "allowed_symbols": ["EURUSD"],
                "max_lot": 0.1,
                "max_risk_percent": 1.0,
                "max_trades_per_day": 3,
                "require_stop_loss": True,
                "duplicate_window_minutes": 60,
            },
            headers=headers,
        )
        assert rule.status_code == 200

        synced = client.get(f"/telegram/messages/{dialog_id}", headers=headers)
        assert synced.status_code == 200

        intents = client.get("/trade-intents", headers=headers)
        assert intents.status_code == 200
        assert any(item["status"] == "executed" and item["payload"]["symbol"] == "EURUSD" for item in intents.json())

        trades = client.get("/trades", headers=headers)
        assert trades.status_code == 200
        assert any(item["symbol"] == "EURUSD" and item["status"] == "submitted" for item in trades.json())
