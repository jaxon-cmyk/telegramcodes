import { FormEvent, useEffect, useState } from "react";
import { api } from "../services/api";
import type { AutomationRule, ExecutedTrade, Message, MT5Account, ParsedSignal, TelegramDialog, TradeIntent, User } from "../types/api";

function useAsyncList<T>(loader: () => Promise<unknown>, fallback: T[] = []) {
  const [items, setItems] = useState<T[]>(fallback);
  const [error, setError] = useState("");
  const refresh = async () => {
    setError("");
    try {
      setItems((await loader()) as T[]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Request failed");
    }
  };
  useEffect(() => {
    void refresh();
  }, []);
  return { items, error, refresh, setItems };
}

export function OverviewPage({ user }: { user: User | null }) {
  return (
    <section className="dashboard-page">
      <div className="dashboard-hero">
        <div>
          <p className="eyebrow">Overview</p>
          <h1>SignalBridge control room</h1>
          <p>Monitor signal feeds, parse trades, enforce risk rules, and keep every MT5 action auditable.</p>
        </div>
        <div className="status-pill">Signed in as {user?.role ?? "user"}</div>
      </div>
      <div className="metric-grid">
        <article><span>Telegram</span><strong>User API login</strong><p>Telethon-ready connection flow with 2FA support.</p></article>
        <article><span>Parser</span><strong>Rules + AI fallback</strong><p>Validated normalized signals before any trade intent.</p></article>
        <article><span>MT5</span><strong>Cloud bridge</strong><p>Modeled after account info, order checks, positions, and history.</p></article>
        <article><span>Access</span><strong>{user?.role === "admin" ? "Admin" : "User"}</strong><p>Invite-only beta with per-user data boundaries.</p></article>
      </div>
      <div className="section-card">
        <h2>Recommended setup path</h2>
        <div className="step-list">
          <span>1. Connect Telegram</span>
          <span>2. Enable signal channels</span>
          <span>3. Connect MT5 bridge account</span>
          <span>4. Create automation rules</span>
          <span>5. Review trade intents and logs</span>
        </div>
      </div>
    </section>
  );
}

export function TelegramPage() {
  const { items, error, refresh } = useAsyncList<TelegramDialog>(() => api.dialogs());
  const [connect, setConnect] = useState({ api_id: "", api_hash: "", phone: "" });
  const [verify, setVerify] = useState({ session_id: "", code: "", password: "" });
  const [message, setMessage] = useState("");

  async function submitConnect(event: FormEvent) {
    event.preventDefault();
    setMessage("");
    try {
      const result = await api.connectTelegram(connect) as { session_id: number; status: string };
      setVerify({ ...verify, session_id: String(result.session_id) });
      setMessage(`Telegram status: ${result.status}. Enter the code Telegram sends to continue.`);
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Telegram connection failed.");
    }
  }

  async function submitVerify(event: FormEvent) {
    event.preventDefault();
    setMessage("");
    try {
      const result = await api.verifyTelegram({ ...verify, session_id: Number(verify.session_id) }) as { status: string };
      setMessage(result.status === "connected" ? "Telegram verified. Dialogs can now be loaded." : `Telegram status: ${result.status}`);
      await refresh();
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Telegram verification failed.");
    }
  }

  async function syncDialog(dialog: TelegramDialog) {
    setMessage("");
    try {
      await api.syncMessages(dialog.dialog_id);
      setMessage(`Synced messages from ${dialog.title}. Valid signals are parsed and auto-traded when an enabled automation rule matches this channel.`);
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Message sync failed.");
    }
  }

  return (
    <section className="dashboard-page">
      <div className="dashboard-hero">
        <div>
          <p className="eyebrow">Telegram</p>
          <h1>Connections and channels</h1>
          <p>Connect a Telegram account, load the channels/groups it can access, enable sources, then sync messages into the parser.</p>
        </div>
        <button onClick={refresh}>Load dialogs</button>
      </div>
      <div className="split">
        <form className="panel" onSubmit={submitConnect}>
          <h2>Connect Telegram</h2>
          <p className="muted">Get these from <a className="text-link" href="https://my.telegram.org" target="_blank" rel="noreferrer">my.telegram.org</a>. Log in, open API development tools, create an app, then copy the API ID and API Hash.</p>
          <div className="help-list">
            <span>Phone must include country code, like +15555550123.</span>
            <span>Telegram sends the verification code after Start verification.</span>
            <span>Private channels appear only if this Telegram account already has access.</span>
          </div>
          <label>API ID<input value={connect.api_id} onChange={(event) => setConnect({ ...connect, api_id: event.target.value })} /></label>
          <label>API Hash<input value={connect.api_hash} onChange={(event) => setConnect({ ...connect, api_hash: event.target.value })} /></label>
          <label>Phone<input value={connect.phone} onChange={(event) => setConnect({ ...connect, phone: event.target.value })} /></label>
          <button>Start verification</button>
        </form>
        <form className="panel" onSubmit={submitVerify}>
          <h2>Verify code</h2>
          <p className="muted">The Session ID fills in after you start verification. Only enter the 2FA password if Telegram asks for one.</p>
          <label>Session ID<input value={verify.session_id} onChange={(event) => setVerify({ ...verify, session_id: event.target.value })} /></label>
          <label>Code<input value={verify.code} onChange={(event) => setVerify({ ...verify, code: event.target.value })} /></label>
          <label>2FA Password<input value={verify.password} onChange={(event) => setVerify({ ...verify, password: event.target.value })} /></label>
          <button>Verify</button>
        </form>
      </div>
      {message && <div className="notice">{message}</div>}
      {error && <div className="empty-state">Connect Telegram first, then click Load dialogs. Server message: {error}</div>}
      <div className="table">
        {items.map((dialog) => (
          <div className="row" key={dialog.dialog_id}>
            <span><strong>{dialog.title}</strong>{dialog.channel_id && <small>Channel ID for automation: {dialog.channel_id}</small>}</span><span>{dialog.kind}</span><span>{dialog.is_enabled ? "Enabled" : "Disabled"}</span>
            <button onClick={() => api.enableChannel(dialog.dialog_id, !dialog.is_enabled).then(refresh)}>Toggle</button>
            <button onClick={() => syncDialog(dialog)}>Sync</button>
          </div>
        ))}
      </div>
      {!items.length && !error && <div className="empty-state">No dialogs loaded yet. Connect Telegram or click Load dialogs after verification.</div>}
    </section>
  );
}

export function MessagesPage() {
  const { items, error, refresh, setItems } = useAsyncList<Message>(() => api.messages());
  const [query, setQuery] = useState("");
  const [notice, setNotice] = useState("");
  async function search() {
    const result = query ? await api.searchMessages(query) : await api.messages();
    return result as Message[];
  }
  return (
    <section className="dashboard-page">
      <div className="dashboard-hero">
        <div>
          <p className="eyebrow">Messages</p>
          <h1>Stored Telegram messages</h1>
          <p>Review synced Telegram posts, search message history, and manually re-run the parser when needed.</p>
        </div>
        <button onClick={refresh}>Refresh</button>
      </div>
      <div className="toolbar"><input placeholder="Search messages" value={query} onChange={(event) => setQuery(event.target.value)} /><button onClick={() => search().then(setItems)}>Search</button><button onClick={refresh}>Refresh</button></div>
      {error && <div className="error">{error}</div>}
      {notice && <div className="notice">{notice}</div>}
      <div className="cards">{items.map((item) => <article key={item.id}><strong>{item.sender_name ?? "Unknown"}</strong><p>{item.text}</p><button onClick={() => api.reparse(item.id).then(() => setNotice("Message parsed. Check the Signals page for the result."))}>Parse</button></article>)}</div>
      {!items.length && <div className="empty-state">No messages yet. Go to Telegram, enable a dialog, then sync messages.</div>}
    </section>
  );
}

export function SignalsPage() {
  const { items, error, refresh } = useAsyncList<ParsedSignal>(() => api.signals());
  return (
    <section className="dashboard-page">
      <div className="dashboard-hero">
        <div>
          <p className="eyebrow">Signals</p>
          <h1>Parsed trade signals</h1>
          <p>Signals are created automatically during Telegram sync, then validated before automation can use them.</p>
        </div>
        <button onClick={refresh}>Refresh signals</button>
      </div>
      {error && <div className="error">{error}</div>}
      <div className="table">{items.map((signal) => <div className="row" key={signal.id}><span>{signal.symbol ?? "No symbol"}</span><span>{signal.side ?? "No side"}</span><span>{signal.status}</span><span>{Math.round(signal.confidence * 100)}%</span><button onClick={() => api.executeTest(signal.id)}>Evaluate trade</button></div>)}</div>
      {!items.length && <div className="empty-state">No parsed signals yet. Sync Telegram messages or manually parse a stored message.</div>}
    </section>
  );
}

export function MT5Page() {
  const { items, error, refresh } = useAsyncList<MT5Account>(() => api.mt5Accounts());
  const [form, setForm] = useState({ name: "", provider: "cloud_bridge", provider_account_id: "", token: "" });
  async function submit(event: FormEvent) {
    event.preventDefault();
    await api.connectMT5({ name: form.name, provider: form.provider, provider_account_id: form.provider_account_id, credentials: { token: form.token } });
    await refresh();
  }
  return (
    <section className="dashboard-page">
      <div className="dashboard-hero">
        <div>
          <p className="eyebrow">MT5</p>
          <h1>Cloud bridge accounts</h1>
          <p>Connect the cloud provider account that can read status and send checked orders to the user's MT5 trading account. Use demo accounts first, then go live only after the bridge health check and order schema are confirmed.</p>
        </div>
      </div>
      <form className="panel" onSubmit={submit}>
        <div className="help-list">
          <span>Name: internal label, like Main Forex Account.</span>
          <span>Provider account ID: copy this from the connected account inside your MT5 bridge provider dashboard.</span>
          <span>Bridge token: provider API token or account token for that MT5 account. Keep it secret.</span>
          <span>If `MT5_BRIDGE_API_KEY` is empty on the server, SignalBridge stays in mock bridge mode and will not place live provider orders.</span>
          <span>After connecting, click Health check and confirm balance/equity/status before creating automation rules.</span>
        </div>
        <label>Name<input value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} /></label>
        <label>Provider account ID<input value={form.provider_account_id} onChange={(event) => setForm({ ...form, provider_account_id: event.target.value })} /></label>
        <label>Bridge token<input value={form.token} onChange={(event) => setForm({ ...form, token: event.target.value })} /></label>
        <button>Connect MT5 account</button>
      </form>
      {error && <div className="error">{error}</div>}
      <div className="table">{items.map((account) => <div className="row" key={account.id}><span><strong>{account.name}</strong><small>MT5 account ID for automation: {account.id}</small></span><span>{account.status}</span><span>{account.balance ?? "-"}</span><button onClick={() => api.mt5Status(account.id).then(refresh)}>Health check</button></div>)}</div>
    </section>
  );
}

export function AutomationPage() {
  const { items, error, refresh } = useAsyncList<AutomationRule>(() => api.automationRules());
  const { items: dialogs, refresh: refreshDialogs } = useAsyncList<TelegramDialog>(() => api.dialogs());
  const { items: accounts, refresh: refreshAccounts } = useAsyncList<MT5Account>(() => api.mt5Accounts());
  const [form, setForm] = useState({ name: "", channel_id: "", mt5_account_id: "", allowed_symbols: "EURUSD,XAUUSD", max_lot: "0.1", max_risk_percent: "1", max_trades_per_day: "3", duplicate_window_minutes: "60" });
  async function submit(event: FormEvent) {
    event.preventDefault();
    await api.createAutomationRule({
      name: form.name,
      channel_id: Number(form.channel_id),
      mt5_account_id: Number(form.mt5_account_id),
      allowed_symbols: form.allowed_symbols.split(",").map((item) => item.trim()).filter(Boolean),
      max_lot: Number(form.max_lot),
      max_risk_percent: Number(form.max_risk_percent),
      max_trades_per_day: Number(form.max_trades_per_day),
      duplicate_window_minutes: Number(form.duplicate_window_minutes),
      require_stop_loss: true
    });
    await refresh();
  }
  async function refreshSetupData() {
    await refreshDialogs();
    await refreshAccounts();
  }
  return (
    <section className="dashboard-page">
      <div className="dashboard-hero">
        <div>
          <p className="eyebrow">Automation</p>
          <h1>Auto-trading risk rules</h1>
          <p>Select the Telegram source and MT5 account, then set the limits that decide whether a parsed signal is allowed to trade automatically.</p>
        </div>
        <button onClick={refreshSetupData}>Refresh setup data</button>
      </div>
      <form className="panel" onSubmit={submit}>
        <p className="muted">When this rule is enabled, valid signals from the selected Telegram channel are automatically checked and sent to the connected MT5 bridge account.</p>
        <div className="help-list">
          <span>Channel: enable it on the Telegram page first.</span>
          <span>MT5 account: connect it on the MT5 Accounts page first.</span>
          <span>Allowed symbols: comma-separated symbols, like EURUSD,XAUUSD.</span>
          <span>Max risk and max lot block oversized trades before order_send.</span>
        </div>
        <label>Name<input value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} /></label>
        <label>Telegram channel
          <select value={form.channel_id} onChange={(event) => setForm({ ...form, channel_id: event.target.value })}>
            <option value="">Select enabled channel</option>
            {dialogs.filter((dialog) => dialog.channel_id).map((dialog) => <option key={dialog.dialog_id} value={dialog.channel_id}>{dialog.title} #{dialog.channel_id}</option>)}
          </select>
        </label>
        <label>MT5 account
          <select value={form.mt5_account_id} onChange={(event) => setForm({ ...form, mt5_account_id: event.target.value })}>
            <option value="">Select MT5 account</option>
            {accounts.map((account) => <option key={account.id} value={account.id}>{account.name} #{account.id}</option>)}
          </select>
        </label>
        <label>Allowed symbols<input value={form.allowed_symbols} onChange={(event) => setForm({ ...form, allowed_symbols: event.target.value })} /></label>
        <label>Max lot<input value={form.max_lot} onChange={(event) => setForm({ ...form, max_lot: event.target.value })} /></label>
        <label>Max risk percent<input value={form.max_risk_percent} onChange={(event) => setForm({ ...form, max_risk_percent: event.target.value })} /></label>
        <label>Max trades per day<input value={form.max_trades_per_day} onChange={(event) => setForm({ ...form, max_trades_per_day: event.target.value })} /></label>
        <label>Duplicate window minutes<input value={form.duplicate_window_minutes} onChange={(event) => setForm({ ...form, duplicate_window_minutes: event.target.value })} /></label>
        <button>Create rule</button>
      </form>
      {error && <div className="error">{error}</div>}
      <div className="table">{items.map((rule) => <div className="row" key={rule.id}><span>{rule.name}</span><span>{rule.is_enabled ? "Enabled" : "Disabled"}</span><span>{rule.allowed_symbols.join(", ")}</span><span>Max lot {rule.max_lot}</span></div>)}</div>
    </section>
  );
}

export function TradeIntentsPage() {
  const { items, error, refresh } = useAsyncList<TradeIntent>(() => api.tradeIntents());
  return <ListPage title="Trade intents" eyebrow="Automation" error={error} refresh={refresh} items={items.map((item) => `${item.status}: ${item.block_reason ?? JSON.stringify(item.payload)}`)} />;
}

export function TradesPage() {
  const { items, error, refresh } = useAsyncList<ExecutedTrade>(() => api.trades());
  return <ListPage title="Trade history" eyebrow="MT5" error={error} refresh={refresh} items={items.map((item) => `${item.symbol} ${item.side} ${item.status} ${item.provider_order_id ?? ""}`)} />;
}

export function LogsPage() {
  const { items, error, refresh } = useAsyncList<{ action: string; entity_type: string; details: Record<string, unknown> }>(() => api.auditLogs());
  return <ListPage title="Execution logs" eyebrow="Audit" error={error} refresh={refresh} items={items.map((item) => `${item.action} on ${item.entity_type}: ${JSON.stringify(item.details)}`)} />;
}

export function SetupGuidePage() {
  return (
    <section className="dashboard-page">
      <div className="dashboard-hero">
        <div>
          <p className="eyebrow">Setup Guide</p>
          <h1>Credentials and launch checklist</h1>
          <p>Use this page when setting up a user from scratch. It shows what each credential is, where to get it, and where it belongs in SignalBridge.</p>
        </div>
      </div>

      <div className="guide-grid">
        <article className="section-card">
          <h2>1. Telegram credentials</h2>
          <ol className="guide-list">
            <li>Open the official Telegram app and confirm this account already belongs to the channels/groups you want to monitor.</li>
            <li>Go to <a className="text-link" href="https://my.telegram.org" target="_blank" rel="noreferrer">my.telegram.org</a> and log in with that same phone number.</li>
            <li>Enter the login code Telegram sends inside the Telegram app.</li>
            <li>Open API development tools, create an app, and use a title like SignalBridge.</li>
            <li>Copy `api_id`, the numeric Telegram app ID, into Telegram API ID.</li>
            <li>Copy `api_hash`, the secret Telegram app key, into Telegram API Hash.</li>
            <li>Enter the Telegram phone number with country code, start verification, then enter the Telegram code.</li>
            <li>Enter the 2FA password only if Telegram asks for it.</li>
            <li>Load dialogs, then enable only the channels/groups this user wants SignalBridge to read.</li>
          </ol>
        </article>

        <article className="section-card">
          <h2>2. MT5 bridge credentials</h2>
          <ol className="guide-list">
            <li>Start with a demo MT5 trading account.</li>
            <li>For the MetaApi example, go to <a className="text-link" href="https://app.metaapi.cloud" target="_blank" rel="noreferrer">app.metaapi.cloud</a>, create an account, and copy the API/auth token from the web app.</li>
            <li>In MetaApi, add a MetaTrader account: platform mt5, broker server name, MT5 login number, and the password MetaApi requires.</li>
            <li>Use a master/trading password only if SignalBridge should place trades. Investor passwords are read-only.</li>
            <li>Deploy/connect the account and wait until MetaApi shows it as connected.</li>
            <li>Copy the MetaApi trading account id into SignalBridge Provider account ID.</li>
            <li>Copy the MetaApi API/auth token into Bridge token.</li>
            <li>On the server, set `MT5_BRIDGE_API_KEY` to the provider token and `MT5_BRIDGE_BASE_URL` to the provider API base URL.</li>
            <li>Click Health check in MT5 Accounts and confirm connected status, balance, or equity before automation.</li>
          </ol>
        </article>

        <article className="section-card">
          <h2>3. Automation rules</h2>
          <ol className="guide-list">
            <li>Enable a Telegram channel first so it receives a Channel ID.</li>
            <li>Connect an MT5 account first so it appears in the MT5 account dropdown.</li>
            <li>Create a rule for that channel/account pair.</li>
            <li>Set allowed symbols, max lot, max risk percent, max trades per day, and duplicate window.</li>
            <li>When messages sync, matching valid signals auto-trade only if every rule passes.</li>
          </ol>
        </article>

        <article className="section-card">
          <h2>4. Server secrets</h2>
          <ol className="guide-list">
            <li>`JWT_SECRET`: long random string for login tokens.</li>
            <li>`ENCRYPTION_KEY`: Fernet key for Telegram sessions and MT5 tokens.</li>
            <li>`ALLOWED_ORIGINS`: server IP/domain, such as `http://129.146.112.0`.</li>
            <li>`MT5_BRIDGE_BASE_URL`: cloud provider API base URL. For MetaApi provisioning, the docs show `https://mt-provisioning-api-v1.agiliumtrade.agiliumtrade.ai`.</li>
            <li>`MT5_BRIDGE_API_KEY`: server/provider API key from the provider web app. Empty means mock bridge mode.</li>
            <li>Keep backend port 8000 private; nginx should proxy to it locally.</li>
          </ol>
        </article>

        <article className="section-card">
          <h2>5. Before live trading</h2>
          <ol className="guide-list">
            <li>Run the whole flow on a demo MT5 account first.</li>
            <li>Confirm broker symbol names match the allowlist, including suffixes like EURUSD.a or XAUUSDm.</li>
            <li>Keep stop-loss required, max lot low, max risk low, and max trades per day conservative.</li>
            <li>Send one tiny test signal and review Trade Intents, Trade History, and Execution Logs.</li>
            <li>If the provider's order API is different, update `backend/app/services/mt5_bridge.py` before live trading.</li>
          </ol>
        </article>
      </div>
    </section>
  );
}

export function AdminPage({ currentUser }: { currentUser: User }) {
  const { items: users, error, refresh } = useAsyncList<User>(() => api.adminUsers());
  const [email, setEmail] = useState("");
  const [newUser, setNewUser] = useState({ email: "", password: "", role: "user", is_active: true });
  const [passwords, setPasswords] = useState<Record<number, string>>({});
  const [result, setResult] = useState("");
  const [notice, setNotice] = useState("");
  async function createInvite(event: FormEvent) {
    event.preventDefault();
    const invite = await api.createInvite(email) as { code: string };
    setResult(invite.code);
  }
  async function updateUser(id: number, payload: Record<string, unknown>) {
    setNotice("");
    try {
      await api.updateAdminUser(id, payload);
      setNotice("User updated.");
      await refresh();
    } catch (err) {
      setNotice(err instanceof Error ? err.message : "Could not update user");
    }
  }
  async function createUser(event: FormEvent) {
    event.preventDefault();
    setNotice("");
    try {
      await api.createAdminUser(newUser);
      setNotice("User account created.");
      setNewUser({ email: "", password: "", role: "user", is_active: true });
      await refresh();
    } catch (err) {
      setNotice(err instanceof Error ? err.message : "Could not create user");
    }
  }
  async function resetPassword(userId: number) {
    const password = passwords[userId];
    if (!password) {
      setNotice("Enter a new password first.");
      return;
    }
    await updateUser(userId, { password });
    setPasswords({ ...passwords, [userId]: "" });
  }
  return (
    <section className="dashboard-page">
      <div className="dashboard-hero">
        <div>
          <p className="eyebrow">Admin</p>
          <h1>Users and invites</h1>
          <p>Manage invite access, promote trusted users to admin, and deactivate accounts when needed.</p>
        </div>
        <button onClick={refresh}>Refresh users</button>
      </div>

      <div className="admin-grid">
        <form className="panel" onSubmit={createUser}>
          <h2>Create user account</h2>
          <p className="muted">Create a ready-to-use account, set the starting password, choose the role, and decide if the account is active.</p>
          <label>Email<input value={newUser.email} onChange={(event) => setNewUser({ ...newUser, email: event.target.value })} /></label>
          <label>Temporary password<input type="password" value={newUser.password} onChange={(event) => setNewUser({ ...newUser, password: event.target.value })} /></label>
          <label>Role
            <select value={newUser.role} onChange={(event) => setNewUser({ ...newUser, role: event.target.value })}>
              <option value="user">User</option>
              <option value="admin">Admin</option>
            </select>
          </label>
          <label className="inline-check">
            <input type="checkbox" checked={newUser.is_active} onChange={(event) => setNewUser({ ...newUser, is_active: event.target.checked })} />
            Active account
          </label>
          <button>Create user</button>
        </form>

        <form className="panel" onSubmit={createInvite}>
          <h2>Create invite</h2>
          <p className="muted">Use invites when you want the user to choose their own password during registration.</p>
          <label>Email optional<input value={email} onChange={(event) => setEmail(event.target.value)} /></label>
          <button>Create invite</button>
          {result && <div className="notice">Invite code: {result}</div>}
        </form>

        <div className="section-card">
          <h2>Admin safety</h2>
          <p>Admins can change other users between user and admin roles. The API blocks removing your own admin role or deactivating yourself.</p>
        </div>
      </div>

      {error && <div className="error">{error}</div>}
      {notice && <div className={notice.includes("Could not") || notice.includes("cannot") ? "error" : "notice"}>{notice}</div>}

      <div className="data-table">
        <div className="data-row data-head">
          <span>User</span>
          <span>Role</span>
          <span>Status</span>
          <span>Actions</span>
        </div>
        {users.map((item) => (
          <div className="data-row" key={item.id}>
            <span>
              <strong>{item.email}</strong>
              {item.id === currentUser.id && <small>You</small>}
            </span>
            <span className="badge">{item.role}</span>
            <span className={item.is_active ? "badge success" : "badge danger"}>{item.is_active ? "Active" : "Inactive"}</span>
            <span className="action-group">
              <button disabled={item.role === "admin"} onClick={() => updateUser(item.id, { role: "admin" })}>Make admin</button>
              <button disabled={item.role === "user" || item.id === currentUser.id} onClick={() => updateUser(item.id, { role: "user" })}>Make user</button>
              <button disabled={item.id === currentUser.id} onClick={() => updateUser(item.id, { is_active: !item.is_active })}>
                {item.is_active ? "Deactivate" : "Activate"}
              </button>
              <input
                className="compact-input"
                type="password"
                placeholder="New password"
                value={passwords[item.id] ?? ""}
                onChange={(event) => setPasswords({ ...passwords, [item.id]: event.target.value })}
              />
              <button onClick={() => resetPassword(item.id)}>Reset password</button>
            </span>
          </div>
        ))}
      </div>
    </section>
  );
}

function ListPage({ title, eyebrow, items, error, refresh }: { title: string; eyebrow: string; items: string[]; error?: string; refresh: () => Promise<void> }) {
  return (
    <section>
      <div className="page-heading"><p className="eyebrow">{eyebrow}</p><h1>{title}</h1></div>
      <button onClick={refresh}>Refresh</button>
      {error && <div className="error">{error}</div>}
      <div className="cards">{items.map((item, index) => <article key={index}>{item}</article>)}</div>
    </section>
  );
}
