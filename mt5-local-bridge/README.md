# Self-Hosted MetaTrader 5 Bridge

This service runs on the Windows machine where MetaTrader 5 is installed and logged in. The Oracle website calls this bridge when a Telegram signal passes all parser and automation safety checks.

This avoids MetaApi or another paid MT5 API provider. The software path is free, but the Windows machine must stay online.

## Windows Setup

1. Get a Windows VPS or Windows PC that can stay online.
2. Install MetaTrader 5.
3. Open MetaTrader 5.
4. Log in to the user's MT5 demo account first.
5. Confirm the MT5 terminal shows connected prices.
6. Install Python for Windows from `https://www.python.org/downloads/windows`.
7. During Python install, enable Add Python to PATH.
8. Open PowerShell.
9. Go to this bridge folder:

```powershell
cd C:\path\to\telegramcodes\mt5-local-bridge
```

10. Install requirements:

```powershell
python -m pip install -r requirements.txt
```

11. Create a long shared secret.
12. Start the bridge:

```powershell
$env:MT5_BRIDGE_API_KEY="PASTE_LONG_RANDOM_SECRET"
python app.py
```

13. The bridge listens on port `8100`.
14. Test it from the Windows machine:

```powershell
curl -H "Authorization: Bearer PASTE_LONG_RANDOM_SECRET" http://127.0.0.1:8100/health
```

## Oracle Website Setup

On the Oracle Linux server running SignalBridge:

```bash
cd ~/telegramcodes/backend
nano .env
```

Set:

```bash
MT5_BRIDGE_BASE_URL=http://WINDOWS_SERVER_IP:8100
MT5_BRIDGE_API_KEY=PASTE_LONG_RANDOM_SECRET
```

Then restart the backend:

```bash
sudo systemctl restart telegramcodes-backend
```

## SignalBridge User Flow

1. User connects Telegram.
2. User enables the Telegram channel.
3. Admin or user opens MT5 Accounts.
4. Name: friendly label, such as `Shawn Demo MT5`.
5. MT5 login / bridge account ID: MT5 login number or bridge nickname.
6. Bridge token: shared bridge secret.
7. Click Connect MT5 account.
8. Click Health check.
9. Create an automation rule.
10. Sync Telegram messages.
11. Valid signals that pass safety rules are sent to MT5.

## Security

1. Do not expose the bridge to the whole internet if you can avoid it.
2. Allow inbound port `8100` only from the Oracle server IP.
3. Keep the bridge secret private.
4. Test on demo accounts first.
5. Keep stop-loss required in SignalBridge automation rules.
