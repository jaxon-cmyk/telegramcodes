# Telegram-to-MT5 Invite-Only SaaS

Greenfield SaaS scaffold based on the requested plan and the two source references:

- `Rantoniaina/telegram-to-mt5`: React + FastAPI + Telethon-style Telegram connection, dialogs, messages, search, auth, and 2FA flow.
- MQL5 Python Integration docs: account info, terminal info, symbols, order checks, order sending, positions, order history, and deal history. The official Python package connects to a local MT5 terminal, so this app wraps those concepts behind a cloud MT5 bridge for Mac-friendly SaaS use.

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
