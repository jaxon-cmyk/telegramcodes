from typing import Any

import httpx

from app.core.config import get_settings


class MT5Bridge:
    """Cloud bridge abstraction based on MQL5 Python trading concepts.

    Official MQL5 Python docs expose account_info, terminal_info, symbol data,
    order_check/order_send, positions, order history, and deal history against a
    local terminal. This adapter keeps those concepts but sends them to a cloud
    provider so Mac users are not forced to run a local Windows terminal.
    """

    def __init__(self) -> None:
        self.settings = get_settings()

    async def account_status(self, provider_account_id: str) -> dict[str, Any]:
        if not self.settings.mt5_bridge_api_key:
            return {
                "status": "mock_connected",
                "account_info": {"login": provider_account_id, "balance": 10000.0, "equity": 10075.25},
                "terminal_info": {"provider": "cloud_bridge_stub"},
            }
        async with httpx.AsyncClient(base_url=str(self.settings.mt5_bridge_base_url)) as client:
            response = await client.get(
                f"/accounts/{provider_account_id}/status",
                headers={"Authorization": f"Bearer {self.settings.mt5_bridge_api_key}"},
            )
            response.raise_for_status()
            return response.json()

    async def positions(self, provider_account_id: str) -> list[dict[str, Any]]:
        if not self.settings.mt5_bridge_api_key:
            return [{"symbol": "EURUSD", "side": "buy", "volume": 0.1, "profit": 42.5}]
        async with httpx.AsyncClient(base_url=str(self.settings.mt5_bridge_base_url)) as client:
            response = await client.get(
                f"/accounts/{provider_account_id}/positions",
                headers={"Authorization": f"Bearer {self.settings.mt5_bridge_api_key}"},
            )
            response.raise_for_status()
            return response.json()

    async def history(self, provider_account_id: str) -> dict[str, Any]:
        if not self.settings.mt5_bridge_api_key:
            return {"orders": [], "deals": []}
        async with httpx.AsyncClient(base_url=str(self.settings.mt5_bridge_base_url)) as client:
            response = await client.get(
                f"/accounts/{provider_account_id}/history",
                headers={"Authorization": f"Bearer {self.settings.mt5_bridge_api_key}"},
            )
            response.raise_for_status()
            return response.json()

    async def order_check(self, provider_account_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        if not self.settings.mt5_bridge_api_key:
            return {"ok": True, "provider_account_id": provider_account_id, "checked_payload": payload}
        async with httpx.AsyncClient(base_url=str(self.settings.mt5_bridge_base_url)) as client:
            response = await client.post(
                f"/accounts/{provider_account_id}/orders/check",
                json=payload,
                headers={"Authorization": f"Bearer {self.settings.mt5_bridge_api_key}"},
            )
            response.raise_for_status()
            return response.json()

    async def order_send(self, provider_account_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        if not self.settings.mt5_bridge_api_key:
            return {"ok": True, "order_id": "mock-order-1", "provider_account_id": provider_account_id}
        async with httpx.AsyncClient(base_url=str(self.settings.mt5_bridge_base_url)) as client:
            response = await client.post(
                f"/accounts/{provider_account_id}/orders",
                json=payload,
                headers={"Authorization": f"Bearer {self.settings.mt5_bridge_api_key}"},
            )
            response.raise_for_status()
            return response.json()
