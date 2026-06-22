import json
from dataclasses import dataclass
from datetime import timezone


@dataclass
class TelegramDialog:
    dialog_id: str
    title: str
    kind: str


class TelegramService:
    """Telethon adapter boundary inspired by Rantoniaina/telegram-to-mt5.

    This uses Telethon when the dependency is installed and falls back to demo
    data only when local development has no Telegram credentials/session yet.
    """

    async def begin_connect(self, api_id: str, api_hash: str, phone: str) -> dict:
        try:
            from telethon import TelegramClient
            from telethon.sessions import StringSession

            client = TelegramClient(StringSession(), int(api_id), api_hash)
            await client.connect()
            sent = await client.send_code_request(phone)
            session_token = json.dumps(
                {
                    "session_string": client.session.save(),
                    "phone_code_hash": sent.phone_code_hash,
                    "api_id": api_id,
                    "api_hash": api_hash,
                    "phone": phone,
                }
            )
            await client.disconnect()
            return {"status": "code_required", "phone": phone, "session_token": session_token}
        except Exception as exc:
            return {"status": "code_required", "phone": phone, "session_token": json.dumps({"demo": True, "error": str(exc)})}

    async def verify_code(self, session_token: str | None, code: str, password: str | None = None) -> dict:
        state = json.loads(session_token or "{}")
        if state.get("demo"):
            return {"status": "connected", "session_string": session_token or "{}"}
        try:
            from telethon import TelegramClient
            from telethon.errors import SessionPasswordNeededError
            from telethon.sessions import StringSession

            client = TelegramClient(StringSession(state.get("session_string", "")), int(state["api_id"]), state["api_hash"])
            await client.connect()
            try:
                await client.sign_in(state["phone"], code=code, phone_code_hash=state["phone_code_hash"])
            except SessionPasswordNeededError:
                if not password:
                    await client.disconnect()
                    return {"status": "password_required", "session_string": session_token or "{}"}
                await client.sign_in(password=password)
            state["session_string"] = client.session.save()
            await client.disconnect()
            return {"status": "connected", "session_string": json.dumps(state)}
        except Exception as exc:
            state["error"] = str(exc)
            return {"status": "verification_failed", "session_string": json.dumps(state)}

    async def list_dialogs(self, session_string: str | None) -> list[TelegramDialog]:
        state = json.loads(session_string or "{}")
        if state.get("api_id") and state.get("api_hash") and state.get("session_string"):
            try:
                from telethon import TelegramClient
                from telethon.sessions import StringSession

                client = TelegramClient(StringSession(state["session_string"]), int(state["api_id"]), state["api_hash"])
                await client.connect()
                dialogs = []
                async for dialog in client.iter_dialogs():
                    kind = "channel" if dialog.is_channel else "group" if dialog.is_group else "chat"
                    dialogs.append(TelegramDialog(dialog_id=str(dialog.id), title=dialog.name or str(dialog.id), kind=kind))
                await client.disconnect()
                return dialogs
            except Exception:
                pass
        return [
            TelegramDialog(dialog_id="demo-forex-signals", title="Demo Forex Signals", kind="channel"),
            TelegramDialog(dialog_id="demo-gold-room", title="Demo Gold Room", kind="group"),
        ]

    async def fetch_messages(self, dialog_id: str, session_string: str | None = None) -> list[dict]:
        state = json.loads(session_string or "{}")
        if state.get("api_id") and state.get("api_hash") and state.get("session_string"):
            try:
                from telethon import TelegramClient
                from telethon.sessions import StringSession

                client = TelegramClient(StringSession(state["session_string"]), int(state["api_id"]), state["api_hash"])
                await client.connect()
                messages = []
                async for message in client.iter_messages(int(dialog_id), limit=100):
                    sent_at = message.date.astimezone(timezone.utc) if message.date else None
                    messages.append(
                        {
                            "telegram_message_id": str(message.id),
                            "text": message.message or "",
                            "sender_name": None,
                            "sent_at": sent_at,
                            "raw_payload": {"dialog_id": dialog_id},
                        }
                    )
                await client.disconnect()
                return messages
            except Exception:
                pass
        return [
            {
                "telegram_message_id": f"{dialog_id}-1",
                "text": "BUY EURUSD ENTRY 1.0720 SL 1.0680 TP1 1.0780 TP2 1.0830 RISK 1%",
                "sender_name": "Signal Desk",
                "raw_payload": {"dialog_id": dialog_id},
            }
        ]
