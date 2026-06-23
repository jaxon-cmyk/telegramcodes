# Telegram-to-MT5 Invite-Only SaaS

Greenfield SaaS scaffold based on the requested plan and the two source references:

- `Rantoniaina/telegram-to-mt5`: React + FastAPI + Telethon-style Telegram connection, dialogs, messages, search, auth, and 2FA flow.
- [MQL5 Python Integration docs](https://www.mql5.com/en/docs/python_metatrader5): account info, terminal info, symbols, order checks, order sending, positions, order history, and deal history. The official Python package connects to a local MetaTrader 5 terminal, so this app uses MetaApi as the hosted client-facing bridge and keeps a self-hosted bridge as an optional backup.

## Included

- React/TypeScript dashboard with login, invite signup, Telegram, messages, signals, MT5 accounts, automation rules, trade intents, trades, logs, and admin pages.
- FastAPI backend with invite-only auth, admin invites, Telegram routes, message storage, rules-first parser with AI fallback hook, MetaApi MT5 adapter, automation checks, trade intent execution, executed trades, and audit logs.
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

### MetaApi MT5 Credentials

The main client-facing setup uses MetaApi. Clients do not need to run a Windows server. They sign up for MetaApi, connect their MT5 account there, then paste the MetaApi account details into SignalBridge.

Which MetaApi option to use:

1. Use **Regular subscription** first. MetaApi currently lists it at about `$30/month`, includes one free MT account, and has a 7-day trial.
2. Do not start with **Extended subscription** unless the client needs higher limits, dedicated API servers, or priority support.
3. Do not use **MetaApi MetaTrader Manager API** unless you are a broker or broker partner with manager access to MT servers.
4. Tell clients API access can be billed pay-as-you-go on top of the subscription, so they should watch MetaApi usage/billing.
5. For your first live client, use a demo MT5 account through Regular before connecting a live account.

What to tell clients:

1. Go to `https://app.metaapi.cloud`.
2. Create a MetaApi account or log in.
3. Choose **Regular subscription** unless you told them otherwise.
4. Start with a demo MetaTrader 5 account first.
5. In MetaApi, add a MetaTrader account.
6. Choose platform `mt5`.
7. Enter the broker server name exactly as the broker shows it.
8. Enter the MT5 login number from the broker portal, MT5 app, or broker welcome email.
9. Enter the MT5 trading password. Investor passwords are read-only and cannot place trades.
10. Deploy/connect the account in MetaApi.
11. Wait until MetaApi shows the account as connected, deployed, or synchronized.
12. Copy the MetaApi account ID.
13. Copy the MetaApi API/auth token.
14. Open SignalBridge.
15. Go to MT5 Accounts.
16. Name: enter a friendly label, such as `Client Demo MT5`.
17. MetaApi account ID: paste the MetaApi account ID.
18. MetaApi token: paste the MetaApi API/auth token.
19. Click Connect MT5 account.
20. Click Health check.
21. Confirm SignalBridge shows connected status, balance, or equity.

Where to find each MT5/MetaApi value:

| SignalBridge field | Where to find it | What it looks like |
| --- | --- | --- |
| `Name` | You make this up inside SignalBridge | `Client Demo MT5` |
| `MetaApi account ID` | `https://app.metaapi.cloud` -> connected MetaTrader account details | Long UUID-style ID |
| `MetaApi token` | MetaApi web app API/auth token area | Long secret token |
| `MT5_BRIDGE_PROVIDER` | Oracle backend `.env` | `metaapi` |
| `MT5_BRIDGE_BASE_URL` | MetaApi API access page | `https://mt-client-api-v1.new-york.agiliumtrade.ai` or the client's MetaApi region URL |
| `MT5_BRIDGE_API_KEY` | MetaApi API/auth token | Long secret token |
| MT5 login | Broker client portal, MT5 app, or broker welcome email | Account number |
| MT5 server | Broker client portal, MT5 app login screen, or broker welcome email | Server name like `ICMarketsSC-Demo` |
| MT5 password | Broker client portal or broker welcome email | Trading/master password |

Server `.env` for MetaApi:

```bash
MT5_BRIDGE_PROVIDER=metaapi
MT5_BRIDGE_BASE_URL=https://mt-client-api-v1.new-york.agiliumtrade.ai
MT5_BRIDGE_API_KEY=PASTE_METAAPI_TOKEN_HERE
```

Current development behavior:

- If `MT5_BRIDGE_API_KEY` is empty, the app uses a mock bridge response so the workflow can be tested safely.
- Mock mode can create mock trade records, but it does not place real MT5 orders.
- To place real trades through MetaApi, configure `MT5_BRIDGE_PROVIDER=metaapi`, `MT5_BRIDGE_BASE_URL`, and `MT5_BRIDGE_API_KEY`.

Before live trading:

- Confirm the broker symbol names match the rule allowlist. Some brokers use suffixes like `EURUSD.a`, `XAUUSDm`, or `US30.cash`.
- Keep `require_stop_loss` enabled.
- Keep max lot and max risk percent low at first.
- Test with one tiny demo trade.
- Check MetaApi and MT5 history to confirm the order reached the correct MT5 account.
- Check SignalBridge Trade Intents and Execution Logs to confirm why the app allowed or blocked the trade.

### Optional Self-Hosted MT5 Bridge Backup

The `mt5-local-bridge` folder is still included as an advanced backup path. Use it only if you do not want MetaApi and are willing to run MetaTrader 5 on a Windows VPS or Windows PC that stays online. See `mt5-local-bridge/README.md`.

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
- Configure `MT5_BRIDGE_PROVIDER=metaapi`, `MT5_BRIDGE_BASE_URL`, and `MT5_BRIDGE_API_KEY` for MetaApi.
- The Telegram service already contains the Telethon session-string flow; verify it against real Telegram app credentials before production use.
- Use demo MetaApi/MT5 accounts before enabling real auto trading.

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
