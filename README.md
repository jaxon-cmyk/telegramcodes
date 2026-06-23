# Telegram-to-MT5 Invite-Only SaaS

Greenfield SaaS scaffold based on the requested plan and the two source references:

- `Rantoniaina/telegram-to-mt5`: React + FastAPI + Telethon-style Telegram connection, dialogs, messages, search, auth, and 2FA flow.
- [MQL5 Python Integration docs](https://www.mql5.com/en/docs/python_metatrader5): account info, terminal info, symbols, order checks, order sending, positions, order history, and deal history. The official Python package connects to a local MetaTrader 5 terminal, so this app wraps those concepts behind a self-hosted MT5 bridge instead of a paid third-party provider.

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

Where to find each Telegram value:

| SignalBridge field | Where to find it | What it looks like |
| --- | --- | --- |
| `API ID` | `https://my.telegram.org` -> `API development tools` -> created app page -> `api_id` | A number like `12345678` |
| `API Hash` | `https://my.telegram.org` -> `API development tools` -> created app page -> `api_hash` | A long secret text string |
| `Phone` | The Telegram account phone number | `+15555550123` |
| `Code` | Telegram sends it inside the official Telegram app during login | Short one-time login code |
| `2FA Password` | Only the user knows it if Telegram two-step verification is enabled | The account's Telegram cloud password |

Easiest Telegram setup steps:

1. Open the official Telegram mobile or desktop app.
2. Confirm the Telegram account is already inside every private/public channel or group SignalBridge should read.
3. Open a browser and go to `https://my.telegram.org`.
4. Log in with the same Telegram phone number.
5. Open Telegram and copy the login code Telegram sends.
6. Paste that login code into `my.telegram.org`.
7. Click `API development tools`.
8. Click create app or fill out the app form if it appears.
9. App title: enter `SignalBridge` or your company name.
10. Short name: enter `signalbridge` or another simple one-word name.
11. URL/platform/description: use simple business values if Telegram shows those fields.
12. Click create application.
13. On the app page, find `api_id`.
14. Copy `api_id`.
15. In SignalBridge, open the Telegram page.
16. Paste `api_id` into `API ID`.
17. Go back to the Telegram app page on `my.telegram.org`.
18. Find `api_hash`.
19. Copy `api_hash`.
20. In SignalBridge, paste `api_hash` into `API Hash`.
21. In SignalBridge, enter the Telegram phone number with country code.
22. Click Start verification.
23. Open Telegram and copy the new login code.
24. Paste that code into SignalBridge.
25. If SignalBridge asks for `2FA Password`, enter the Telegram two-step verification password.
26. Click Verify.
27. Click Load dialogs.
28. Enable the channels/groups SignalBridge should monitor.
29. Click Sync messages to pull history and begin parsing.

What these values mean:

- `api_id`: Telegram's numeric app ID for the Telegram API app you created.
- `api_hash`: Telegram's secret key for that API app.
- Phone: the real Telegram user account that has access to the channels.
- Login code: the one-time code Telegram sends during sign-in.
- 2FA password: the account password only required if that Telegram account has two-step verification turned on.

After verification:

- Click Load dialogs.
- Toggle the channels/groups you want to monitor.
- The UI shows the internal Channel ID after a dialog is enabled.
- Sync messages to parse signals and trigger automation rules.

### Free Self-Hosted MT5 Bridge Credentials

The app no longer depends on MetaApi or another paid MT5 API provider. The free route is:

1. The website runs on the Oracle server.
2. MetaTrader 5 runs on a Windows VPS or Windows PC.
3. The included `mt5-local-bridge` service runs on that Windows machine.
4. The Oracle backend sends checked trade requests to that bridge over HTTP.
5. The bridge uses the official `MetaTrader5` Python package to talk to the local MetaTrader 5 terminal.

Why this matters: the official MQL5 Python Integration docs say the Python package establishes a connection with the MetaTrader 5 terminal and exposes terminal-backed functions like `account_info`, `terminal_info`, `symbols_get`, `symbol_info_tick`, `order_check`, `order_send`, `positions_get`, `history_orders_get`, and `history_deals_get`. So the free version needs a Windows machine where MT5 is installed and logged in.

How to get the Windows machine:

1. Easiest hosted option: create a second Oracle Cloud instance using a Windows Server image.
2. In Oracle Cloud, create a Compute instance.
3. For image/OS, choose Windows Server 2022 or Windows Server 2025.
4. Use Remote Desktop/RDP to log into it.
5. Install MetaTrader 5, Python, and `mt5-local-bridge` on that Windows instance.
6. Keep that Windows instance running 24/7 so trades can execute.
7. Lowest-cost local option: use a spare Windows PC, but it must stay awake, online, and logged into MT5.
8. Do not use the Oracle Linux web server itself for MT5 execution. The official Python integration needs the MetaTrader 5 terminal, which is a Windows desktop app.

Where to find each MT5 value:

| SignalBridge field | Where to find it | What it looks like |
| --- | --- | --- |
| `Name` | You make this up inside SignalBridge | `Shawn Demo MT5` |
| `MT5 login / bridge account ID` | Broker portal, MT5 title bar/account info, or bridge operator notes | MT5 login number or nickname |
| `Bridge token` | The `MT5_BRIDGE_API_KEY` secret you set on the bridge and Oracle backend | Long random secret |
| `MT5_BRIDGE_API_KEY` | You create this secret yourself | Long random secret |
| `MT5_BRIDGE_BASE_URL` | Public/private URL of the Windows bridge service | `http://WINDOWS_SERVER_IP:8100` |
| MT5 login | Broker client portal, MT5 app, or broker welcome email | Account number |
| MT5 server | Broker client portal, MT5 app login screen, or broker welcome email | Server name like `ICMarketsSC-Demo` |
| MT5 password | Broker client portal or broker welcome email | Trading/master password or investor password |

### Step-by-Step Free MT5 Setup

Follow this exact flow for each MT5 account:

1. Start with a demo MetaTrader 5 account first.
2. Get a Windows VPS or Windows PC that can stay online.
3. On that Windows machine, install MetaTrader 5 from the broker or from `https://www.metatrader5.com`.
4. Open MetaTrader 5.
5. Log in to the demo MT5 account using the broker login number, password, and server name.
6. Confirm MT5 shows prices moving and the account is connected.
7. Install Python for Windows from `https://www.python.org/downloads/windows`.
8. During Python install, check Add Python to PATH.
9. Open PowerShell.
10. Install the bridge requirements:

```powershell
cd C:\path\to\telegramcodes\mt5-local-bridge
python -m pip install -r requirements.txt
```

11. Create a long shared bridge secret, such as a random password.
12. Start the Windows bridge:

```powershell
$env:MT5_BRIDGE_API_KEY="PASTE_LONG_RANDOM_SECRET"
python app.py
```

13. On the Oracle server, open `backend/.env`.
14. Set the bridge URL and the same shared secret:

```bash
MT5_BRIDGE_BASE_URL=http://WINDOWS_SERVER_IP:8100
MT5_BRIDGE_API_KEY=PASTE_LONG_RANDOM_SECRET
```

15. Restart the Oracle backend.
16. Open SignalBridge.
17. Go to MT5 Accounts.
18. Name: enter a friendly label, such as `Shawn Demo MT5`.
19. MT5 login / bridge account ID: enter the MT5 login number or bridge nickname.
20. Bridge token: paste the same shared bridge secret.
21. Click Connect MT5 account.
22. Click Health check.
23. Confirm SignalBridge shows connected status, balance/equity, or terminal info.
24. Open Automation.
25. Select the Telegram channel.
26. Select the MT5 account.
27. Set conservative risk values.
28. Create the rule.
29. Send one demo signal and check Trade Intents, Trade History, and Execution Logs.

Important free-hosting note: the software path is free, but the bridge still needs a Windows machine/VPS that stays online. If the Windows machine is off, asleep, disconnected, or MT5 is closed, auto trading cannot execute.

### Step-by-Step MT5 Setup Checklist

Follow this exact flow for each MT5 account:

1. Start with a demo MT5 account first. Do not connect a live account until the full flow has been tested.
2. Install and log into MetaTrader 5 on the Windows bridge machine.
3. Start `mt5-local-bridge` on that same Windows machine.
4. On the Oracle server, set bridge values in `backend/.env`:

```bash
MT5_BRIDGE_BASE_URL=http://WINDOWS_SERVER_IP:8100
MT5_BRIDGE_API_KEY=YOUR_SHARED_BRIDGE_SECRET
```

5. Restart the backend service after changing `.env`.
6. In SignalBridge, open MT5 Accounts and click Connect MT5 account.
7. Click Health check. The account should show connected status, balance, equity, or terminal info.
8. Open Automation, select the Telegram channel and the MT5 account, then create a rule with low demo limits.
9. Sync a test Telegram message and confirm the Trade Intents, Trade History, and Execution Logs pages show the full decision trail.

Current development behavior:

- If `MT5_BRIDGE_API_KEY` is empty, the app uses a mock bridge response so the workflow can be tested safely.
- Mock bridge mode can create mock trade records, but it does not place real MT5 orders.
- To place real trades, configure `MT5_BRIDGE_BASE_URL`, set `MT5_BRIDGE_API_KEY`, run the Windows bridge, and keep MetaTrader 5 open.

Before live trading:

- Confirm the broker symbol names match the rule allowlist. Some brokers use suffixes like `EURUSD.a`, `XAUUSDm`, or `US30.cash`.
- Keep `require_stop_loss` enabled.
- Keep max lot and max risk percent low at first.
- Test with one tiny demo trade.
- Check MetaTrader 5 history to confirm the order reached the correct MT5 account.
- Check SignalBridge Trade Intents and Execution Logs to confirm why the app allowed or blocked the trade.
- Keep the Windows bridge URL private or protect it with firewall rules plus the bridge secret.

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
- Configure `MT5_BRIDGE_BASE_URL` and `MT5_BRIDGE_API_KEY` for the self-hosted Windows MT5 bridge.
- The Telegram service already contains the Telethon session-string flow; verify it against real Telegram app credentials before production use.
- Keep MetaTrader 5 open and logged in on the Windows bridge machine before enabling real auto trading.

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
