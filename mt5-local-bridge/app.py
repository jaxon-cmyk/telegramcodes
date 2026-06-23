import os
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

try:
    import MetaTrader5 as mt5
except ImportError:  # pragma: no cover - this service runs on Windows with MT5 installed.
    mt5 = None


API_KEY = os.getenv("MT5_BRIDGE_API_KEY", "")
MT5_PATH = os.getenv("MT5_TERMINAL_PATH")

app = FastAPI(title="Self-hosted MT5 Bridge")


class TradePayload(BaseModel):
    symbol: str
    side: str
    volume: float
    entry: float | None = None
    stop_loss: float | None = None
    take_profit: float | None = None
    take_profits: list[float] | None = None
    comment: str | None = "SignalBridge"


def require_auth(authorization: str | None) -> None:
    if not API_KEY:
        return
    if authorization != f"Bearer {API_KEY}":
        raise HTTPException(status_code=401, detail="Invalid bridge token")


def ensure_mt5() -> None:
    if mt5 is None:
        raise HTTPException(status_code=500, detail="MetaTrader5 Python package is not installed")
    ok = mt5.initialize(path=MT5_PATH) if MT5_PATH else mt5.initialize()
    if not ok:
        raise HTTPException(status_code=503, detail={"message": "MT5 initialize failed", "last_error": mt5.last_error()})


def as_dict(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if hasattr(value, "_asdict"):
        return dict(value._asdict())
    if isinstance(value, dict):
        return value
    return {"value": value}


def order_type(side: str) -> int:
    normalized = side.lower()
    if normalized == "buy":
        return mt5.ORDER_TYPE_BUY
    if normalized == "sell":
        return mt5.ORDER_TYPE_SELL
    raise HTTPException(status_code=400, detail="side must be buy or sell")


def build_order(payload: TradePayload) -> dict[str, Any]:
    tick = mt5.symbol_info_tick(payload.symbol)
    if tick is None:
        raise HTTPException(status_code=400, detail=f"No tick data for {payload.symbol}")
    side = payload.side.lower()
    price = payload.entry or (tick.ask if side == "buy" else tick.bid)
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": payload.symbol,
        "volume": payload.volume,
        "type": order_type(payload.side),
        "price": price,
        "deviation": 20,
        "comment": payload.comment or "SignalBridge",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    if payload.stop_loss:
        request["sl"] = payload.stop_loss
    take_profit = payload.take_profit or (payload.take_profits[0] if payload.take_profits else None)
    if take_profit:
        request["tp"] = take_profit
    return request


@app.get("/health")
def health(authorization: str | None = Header(default=None)) -> dict[str, Any]:
    require_auth(authorization)
    ensure_mt5()
    return {"ok": True, "terminal_info": as_dict(mt5.terminal_info()), "account_info": as_dict(mt5.account_info())}


@app.get("/accounts/{account_id}/status")
def account_status(account_id: str, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    require_auth(authorization)
    ensure_mt5()
    account = as_dict(mt5.account_info())
    terminal = as_dict(mt5.terminal_info())
    return {"status": "connected", "account_id": account_id, "account_info": account, "terminal_info": terminal}


@app.get("/accounts/{account_id}/positions")
def positions(account_id: str, authorization: str | None = Header(default=None)) -> list[dict[str, Any]]:
    require_auth(authorization)
    ensure_mt5()
    return [as_dict(item) for item in mt5.positions_get() or []]


@app.get("/accounts/{account_id}/history")
def history(account_id: str, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    require_auth(authorization)
    ensure_mt5()
    to_date = datetime.now(timezone.utc)
    from_date = to_date - timedelta(days=30)
    return {
        "orders": [as_dict(item) for item in mt5.history_orders_get(from_date, to_date) or []],
        "deals": [as_dict(item) for item in mt5.history_deals_get(from_date, to_date) or []],
    }


@app.post("/accounts/{account_id}/orders/check")
def check_order(account_id: str, payload: TradePayload, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    require_auth(authorization)
    ensure_mt5()
    request = build_order(payload)
    result = mt5.order_check(request)
    return {"ok": bool(result and result.retcode == mt5.TRADE_RETCODE_DONE), "request": request, "result": as_dict(result)}


@app.post("/accounts/{account_id}/orders")
def send_order(account_id: str, payload: TradePayload, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    require_auth(authorization)
    ensure_mt5()
    request = build_order(payload)
    result = mt5.order_send(request)
    result_dict = as_dict(result)
    ok = bool(result and result.retcode == mt5.TRADE_RETCODE_DONE)
    return {"ok": ok, "order_id": str(result_dict.get("order", "")), "request": request, "result": result_dict}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8100")))
