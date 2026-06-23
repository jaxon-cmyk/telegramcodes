from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

from app.core.config import get_settings


class MT5Bridge:
    """MT5 bridge abstraction based on MQL5 and MetaApi trading concepts.

    MetaApi is the default hosted provider. The self-hosted Windows bridge is
    still supported by setting MT5_BRIDGE_PROVIDER=self_hosted.
    """

    def __init__(self) -> None:
        self.settings = get_settings()

    @property
    def is_metaapi(self) -> bool:
        return self.settings.mt5_bridge_provider == "metaapi"

    def _headers(self) -> dict[str, str]:
        if self.is_metaapi:
            return {"auth-token": self.settings.mt5_bridge_api_key or ""}
        return {"Authorization": f"Bearer {self.settings.mt5_bridge_api_key}"}

    def _metaapi_trade_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        take_profits = payload.get("take_profits") or []
        body = {
            "actionType": "ORDER_TYPE_BUY" if (payload.get("side") or "").lower() == "buy" else "ORDER_TYPE_SELL",
            "symbol": payload.get("symbol"),
            "volume": payload.get("volume"),
        }
        if payload.get("stop_loss"):
            body["stopLoss"] = payload["stop_loss"]
        if take_profits:
            body["takeProfit"] = take_profits[0]
        return body

    async def account_status(self, provider_account_id: str) -> dict[str, Any]:
        if not self.settings.mt5_bridge_api_key:
            return {
                "status": "mock_connected",
                "account_info": {"login": provider_account_id, "balance": 10000.0, "equity": 10075.25},
                "terminal_info": {"bridge": "mock_self_hosted_mt5_bridge"},
            }
        async with httpx.AsyncClient(base_url=str(self.settings.mt5_bridge_base_url)) as client:
            if self.is_metaapi:
                response = await client.get(
                    f"/users/current/accounts/{provider_account_id}/account-information",
                    headers=self._headers(),
                )
                response.raise_for_status()
                return {"status": "connected", "account_info": response.json(), "terminal_info": {"provider": "metaapi"}}
            response = await client.get(
                f"/accounts/{provider_account_id}/status",
                headers=self._headers(),
            )
            response.raise_for_status()
            return response.json()

    async def positions(self, provider_account_id: str) -> list[dict[str, Any]]:
        if not self.settings.mt5_bridge_api_key:
            return [{"symbol": "EURUSD", "side": "buy", "volume": 0.1, "profit": 42.5}]
        async with httpx.AsyncClient(base_url=str(self.settings.mt5_bridge_base_url)) as client:
            if self.is_metaapi:
                response = await client.get(
                    f"/users/current/accounts/{provider_account_id}/positions",
                    headers=self._headers(),
                )
                response.raise_for_status()
                return response.json()
            response = await client.get(
                f"/accounts/{provider_account_id}/positions",
                headers=self._headers(),
            )
            response.raise_for_status()
            return response.json()

    async def history(self, provider_account_id: str) -> dict[str, Any]:
        if not self.settings.mt5_bridge_api_key:
            return {"orders": [], "deals": []}
        async with httpx.AsyncClient(base_url=str(self.settings.mt5_bridge_base_url)) as client:
            if self.is_metaapi:
                end = datetime.now(timezone.utc)
                start = end - timedelta(days=30)
                start_text = start.isoformat(timespec="milliseconds").replace("+00:00", "Z")
                end_text = end.isoformat(timespec="milliseconds").replace("+00:00", "Z")
                orders = await client.get(
                    f"/users/current/accounts/{provider_account_id}/history-orders/time/{start_text}/{end_text}",
                    headers=self._headers(),
                )
                deals = await client.get(
                    f"/users/current/accounts/{provider_account_id}/history-deals/time/{start_text}/{end_text}",
                    headers=self._headers(),
                )
                orders.raise_for_status()
                deals.raise_for_status()
                return {"orders": orders.json(), "deals": deals.json()}
            response = await client.get(
                f"/accounts/{provider_account_id}/history",
                headers=self._headers(),
            )
            response.raise_for_status()
            return response.json()

    async def order_check(self, provider_account_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        if not self.settings.mt5_bridge_api_key:
            return {"ok": True, "provider_account_id": provider_account_id, "checked_payload": payload}
        if self.is_metaapi:
            return {"ok": True, "provider_account_id": provider_account_id, "checked_payload": self._metaapi_trade_payload(payload)}
        async with httpx.AsyncClient(base_url=str(self.settings.mt5_bridge_base_url)) as client:
            response = await client.post(
                f"/accounts/{provider_account_id}/orders/check",
                json=payload,
                headers=self._headers(),
            )
            response.raise_for_status()
            return response.json()

    async def order_send(self, provider_account_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        if not self.settings.mt5_bridge_api_key:
            return {"ok": True, "order_id": "mock-order-1", "provider_account_id": provider_account_id}
        async with httpx.AsyncClient(base_url=str(self.settings.mt5_bridge_base_url)) as client:
            if self.is_metaapi:
                response = await client.post(
                    f"/users/current/accounts/{provider_account_id}/trade",
                    json=self._metaapi_trade_payload(payload),
                    headers=self._headers(),
                )
                response.raise_for_status()
                data = response.json()
                return {"ok": data.get("stringCode") == "TRADE_RETCODE_DONE", "order_id": data.get("orderId"), **data}
            response = await client.post(
                f"/accounts/{provider_account_id}/orders",
                json=payload,
                headers=self._headers(),
            )
            response.raise_for_status()
            return response.json()
