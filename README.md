# Telegram-to-MT5 Invite-Only SaaS

Greenfield SaaS scaffold based on the requested plan and the two source references:

- `Rantoniaina/telegram-to-mt5`: React + FastAPI + Telethon-style Telegram connection, dialogs, messages, search, auth, and 2FA flow.
- [MQL5 Python Integration docs](https://www.mql5.com/en/docs/python_metatrader5): account info, terminal info, symbols, order checks, order sending, positions, order history, and deal history. The official Python package connects to a local MT5 terminal, so this app wraps those concepts behind a cloud MT5 bridge for Mac-friendly SaaS use.

## Included

- React/TypeScript dashboard with login, invite signup, Telegram, messages, signals, MT5 accounts, automation rules, trade intents, trades, logs, and admin pages.
- FastAPI backend with invite-only auth, admin invites, Telegram routes, message storage, rules-first parser with AI fallback hook, MT5 cloud bridge adapter, automation checks, trade intent execution, executed trades, and audit logs.
- SQLAlchemy models for User, Invite, TelegramSession, TelegramChannel, TelegramMessage, ParsedSignal, MT5Account, AutomationRule, TradeIntent, ExecutedTrade, and AuditLog.
- SQLite local default for quick development and PostgreSQL-ready `DATABASE_URL` for Oracle production.
- Background worker entrypoint for Telegram sync/listening, parsing, MT5 health checks, trade queue processing, and audit logging.

## Local Development

Backend:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python run.py
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Local app URLs:

- Frontend: `http://localhost:5173`
- Backend health: `http://localhost:8000/health`
- API docs: `http://localhost:8000/docs`

Default bootstrap admin:

- Email: `admin@example.com`
- Password: `ChangeMe123!`

Change these in `backend/.env` before any real deployment.

## Admin User Onboarding

Admins have two ways to add users:

- Create invite: generates an invite code so the user can register and choose their own password.
- Create user account: creates a ready-to-use account immediately with email, temporary password, role, and active/inactive status.

Admins can also manage existing users from the Admin page:

- Change role between `user` and `admin`.
- Activate or deactivate accounts.
- Reset a user's password by setting a new temporary password.

The backend blocks admins from deactivating themselves or removing their own admin role.

## Credential Checklist

Use this checklist when setting up a real account or walking a user through onboarding.

### Server/Admin Credentials

These are configured by the site owner in `backend/.env` on the Oracle server.

- `JWT_SECRET`: create a long random string. Used to sign login tokens.
- `ENCRYPTION_KEY`: generate with `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`. Used to encrypt Telegram sessions and MT5 bridge credentials.
- `BOOTSTRAP_ADMIN_EMAIL`: first admin email.
- `BOOTSTRAP_ADMIN_PASSWORD`: first admin password. Change it before inviting users.
- `ALLOWED_ORIGINS`: use `http://YOUR_SERVER_IP` until there is a domain.

### Telegram User Credentials

Each user gets these from Telegram:

1. Go to `https://my.telegram.org`.
2. Log in with the Telegram phone number that is already inside the signal channels.
3. Click API development tools.
4. Create an app. App title/short name can be anything recognizable, such as `SignalBridge`.
5. Copy `api_id` into SignalBridge `API ID`.
6. Copy `api_hash` into SignalBridge `API Hash`.
7. Enter the Telegram phone number with country code, such as `+15555550123`.
8. Click Start verification.
9. Enter the Telegram login code.
10. Enter 2FA password only if Telegram asks for it.

After verification:

- Click Load dialogs.
- Toggle the channels/groups you want to monitor.
- The UI shows the internal Channel ID after a dialog is enabled.
- Sync messages to parse signals and trigger automation rules.

### MT5 Bridge Credentials

The app is built for a cloud MT5 bridge/provider so Mac users do not need to run a local Windows MT5 terminal.

Why this matters: the official MQL5 Python Integration docs say the Python package establishes a connection with the MetaTrader 5 terminal and exposes terminal-backed functions like `account_info`, `terminal_info`, `symbols_get`, `symbol_info_tick`, `order_check`, `order_send`, `positions_get`, `history_orders_get`, and `history_deals_get`. That is great for a Windows machine running MT5 locally, but it is not the clean SaaS flow for Mac users logging into a website. SignalBridge keeps those same trading concepts, but sends them through `backend/app/services/mt5_bridge.py` to a cloud bridge/provider instead.

Use a cloud provider that supports MT5 account status, positions, history, market data, order checks, and trade execution. MetaApi is one example of this provider style: its docs describe a cloud API for MetaTrader 4/5, adding a MetaTrader account to the provider app, then using REST or WebSocket APIs for account information, positions, history, market data, and trade execution.

You need these from the chosen MT5 bridge provider:

- Provider account/login ID: put this in `Provider account ID`.
- Provider API token/account token: put this in `Bridge token`.
- Optional global provider API key: set `MT5_BRIDGE_API_KEY` in `backend/.env` if your provider uses a server-level key.
- Provider base URL: set `MT5_BRIDGE_BASE_URL` in `backend/.env`.

### Step-by-Step MT5 Setup

Follow this exact flow for each MT5 account:

1. Start with a demo MT5 account first. Do not connect a live account until the full flow has been tested.
2. Choose the cloud MT5 bridge/provider the business will use.
3. Create or log into the provider account.
4. In the provider dashboard, add a MetaTrader account.
5. Enter the broker name/server, MT5 login number, and the MT5 password required by that provider.
6. Wait until the provider shows the account as connected, deployed, or synchronized.
7. Copy the provider's account ID for that connected MT5 account. In SignalBridge, paste it into `Provider account ID`.
8. Copy the provider API token or account token. In SignalBridge, paste it into `Bridge token`.
9. On the Oracle server, set provider-wide values in `backend/.env`:

```bash
MT5_BRIDGE_BASE_URL=https://YOUR_PROVIDER_API_BASE_URL
MT5_BRIDGE_API_KEY=YOUR_PROVIDER_SERVER_API_KEY
```

10. Restart the backend service after changing `.env`.
11. In SignalBridge, open MT5 Accounts and click Connect MT5 account.
12. Click Health check. The account should show connected status, balance, equity, or any fields the provider returns.
13. Open Automation, select the Telegram channel and the MT5 account, then create a rule with low demo limits.
14. Sync a test Telegram message and confirm the Trade Intents, Trade History, and Execution Logs pages show the full decision trail.

Current development behavior:

- If `MT5_BRIDGE_API_KEY` is empty, the app uses a mock bridge response so the workflow can be tested safely.
- Mock bridge mode can create mock trade records, but it does not place real provider orders.
- To place real trades, configure the real provider URL/key and verify the provider's order schema matches `backend/app/services/mt5_bridge.py`.

Before live trading:

- Confirm the broker symbol names match the rule allowlist. Some brokers use suffixes like `EURUSD.a`, `XAUUSDm`, or `US30.cash`.
- Keep `require_stop_loss` enabled.
- Keep max lot and max risk percent low at first.
- Test with one tiny demo trade.
- Check the provider dashboard to confirm the order reached the correct MT5 account.
- Check SignalBridge Trade Intents and Execution Logs to confirm why the app allowed or blocked the trade.
- If the provider uses a different endpoint shape than the default adapter, update `backend/app/services/mt5_bridge.py` before enabling real trading.

### Automation Rule IDs

The Automation page now uses dropdowns where possible.

- Telegram channel: enable it on the Telegram page first.
- MT5 account: connect it on the MT5 Accounts page first.
- Allowed symbols: comma-separated values such as `EURUSD,XAUUSD`.
- Max lot: highest allowed order size.
- Max risk percent: highest allowed signal risk.
- Max trades per day: daily cap per rule.
- Duplicate window minutes: blocks repeated signals for the same symbol/side.

Auto trading starts only when all of these exist:

- Verified Telegram account.
- Enabled Telegram channel.
- Connected MT5 bridge account.
- Enabled automation rule for that exact channel/account.
- Valid parsed signal with required fields.
- Risk checks pass.

## Oracle Server Deployment by IP

These steps deploy the app at `http://YOUR_SERVER_IP` with nginx serving the built frontend and proxying API routes to FastAPI on `127.0.0.1:8000`.

Install server packages on Oracle Linux:

```bash
sudo dnf install -y git nginx python3 python3-pip
curl -fsSL https://rpm.nodesource.com/setup_20.x | sudo bash -
sudo dnf install -y nodejs
```

Clone or update the repo:

```bash
git clone https://github.com/jaxon-cmyk/telegramcodes.git
cd telegramcodes
```

Set up the backend:

```bash
cd ~/telegramcodes/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `backend/.env`:

```bash
nano .env
```

Minimum production values:

```env
DATABASE_URL=sqlite:///./dev.db
JWT_SECRET=replace-with-a-long-random-secret
ENCRYPTION_KEY=replace-with-fernet-key
ALLOWED_ORIGINS=http://YOUR_SERVER_IP
```

Generate an encryption key:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Create `/etc/systemd/system/telegramcodes-backend.service`:

```ini
[Unit]
Description=Telegramcodes FastAPI backend
After=network.target

[Service]
User=opc
WorkingDirectory=/home/opc/telegramcodes/backend
Environment=PYTHONPATH=/home/opc/telegramcodes/backend
ExecStart=/home/opc/telegramcodes/backend/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

Start the backend:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now telegramcodes-backend
curl http://127.0.0.1:8000/health
```

Build the frontend:

```bash
cd ~/telegramcodes/frontend
npm install
npm run build
```

Create `/etc/nginx/conf.d/telegramcodes.conf`:

```nginx
server {
    listen 80;
    server_name _;

    root /home/opc/telegramcodes/frontend/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location ~ ^/(auth|admin|telegram|messages|signals|mt5|automation-rules|trade-intents|trades|invites|audit-logs|health) {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable nginx:

```bash
sudo nginx -t
sudo systemctl enable --now nginx
sudo systemctl reload nginx
```

Open the server firewall if `firewalld` is running:

```bash
sudo firewall-cmd --state
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --reload
```

Oracle Cloud Network Security Group inbound rules:

- TCP `22` from your IP for SSH and VS Code.
- TCP `80` from `0.0.0.0/0` for the website.
- TCP `443` from `0.0.0.0/0` later when HTTPS is configured.

Do not expose `8000`, `5173`, `5432`, or worker/internal ports publicly.

Verify:

```bash
curl http://127.0.0.1:8000/health
curl http://YOUR_SERVER_IP/health
```

Then open `http://YOUR_SERVER_IP` in a browser.

## Production Notes

- Set `DATABASE_URL` to PostgreSQL on Oracle.
- Set a stable `ENCRYPTION_KEY` generated by `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`.
- Set a strong `JWT_SECRET`.
- Configure `ALLOWED_ORIGINS` to the production frontend domain.
- Configure `MT5_BRIDGE_BASE_URL` and `MT5_BRIDGE_API_KEY` for the chosen cloud MT5 provider.
- The Telegram service already contains the Telethon session-string flow; verify it against real Telegram app credentials before production use.
- Keep the MT5 adapter provider-based unless you intentionally add a separate Windows terminal/agent option.

## Telegram Setup

Each user connects their own Telegram account from the dashboard:

1. Go to `https://my.telegram.org`.
2. Log in with the Telegram phone number.
3. Open API development tools.
4. Create an app and copy the `api_id` and `api_hash`.
5. In SignalBridge, open Telegram, enter API ID, API hash, and the phone number.
6. Enter the verification code sent by Telegram.
7. If the account has 2FA enabled, enter the Telegram 2FA password.
8. Load dialogs, enable the channels/groups to monitor, then click Sync.

Notes:

- Private channels only appear if the connected Telegram account already has access.
- Synced Telegram messages are stored per user and automatically parsed into signal records.
- The demo fallback exists so the app can be tested before real Telegram credentials are entered.
- Real production use should be tested with a dedicated Telegram account before inviting users.

## Auto Trading Behavior

Auto trading is enabled through Automation rules:

1. Connect Telegram.
2. Enable a Telegram channel/group.
3. Connect an MT5 bridge account.
4. Create an enabled automation rule for that channel and MT5 account.
5. Set safety limits: allowed symbols, max lot, max risk percent, max trades per day, stop-loss required, and duplicate window.
6. Sync Telegram messages.

When a new message syncs:

- The message is stored under the signed-in user.
- The parser creates a `ParsedSignal`.
- If the signal is valid and an enabled rule matches the source channel, the app creates a `TradeIntent`.
- The automation engine checks all safety limits.
- If checks pass, the MT5 bridge runs `order_check` and `order_send`.
- The app stores an `ExecutedTrade` and audit log.

If a signal fails safety checks, it is stored as a blocked trade intent with the exact reason. Do not expose the backend port publicly; nginx should proxy API traffic to `127.0.0.1:8000`.
