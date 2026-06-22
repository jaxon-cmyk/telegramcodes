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
    <section>
      <div className="page-heading"><p className="eyebrow">Overview</p><h1>SignalBridge control room</h1></div>
      <div className="metric-grid">
        <article><span>Telegram</span><strong>User API login</strong><p>Telethon-ready connection flow with 2FA support.</p></article>
        <article><span>Parser</span><strong>Rules + AI fallback</strong><p>Validated normalized signals before any trade intent.</p></article>
        <article><span>MT5</span><strong>Cloud bridge</strong><p>Modeled after account info, order checks, positions, and history.</p></article>
        <article><span>Access</span><strong>{user?.role ?? "user"}</strong><p>Invite-only beta with per-user data boundaries.</p></article>
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
    const result = await api.connectTelegram(connect) as { session_id: number; status: string };
    setVerify({ ...verify, session_id: String(result.session_id) });
    setMessage(`Telegram status: ${result.status}`);
  }

  async function submitVerify(event: FormEvent) {
    event.preventDefault();
    await api.verifyTelegram({ ...verify, session_id: Number(verify.session_id) });
    setMessage("Telegram verified. Dialogs can now be loaded.");
    await refresh();
  }

  return (
    <section>
      <div className="page-heading"><p className="eyebrow">Telegram</p><h1>Connections and channels</h1></div>
      <div className="split">
        <form className="panel" onSubmit={submitConnect}>
          <h2>Connect Telegram</h2>
          <label>API ID<input value={connect.api_id} onChange={(event) => setConnect({ ...connect, api_id: event.target.value })} /></label>
          <label>API Hash<input value={connect.api_hash} onChange={(event) => setConnect({ ...connect, api_hash: event.target.value })} /></label>
          <label>Phone<input value={connect.phone} onChange={(event) => setConnect({ ...connect, phone: event.target.value })} /></label>
          <button>Start verification</button>
        </form>
        <form className="panel" onSubmit={submitVerify}>
          <h2>Verify code</h2>
          <label>Session ID<input value={verify.session_id} onChange={(event) => setVerify({ ...verify, session_id: event.target.value })} /></label>
          <label>Code<input value={verify.code} onChange={(event) => setVerify({ ...verify, code: event.target.value })} /></label>
          <label>2FA Password<input value={verify.password} onChange={(event) => setVerify({ ...verify, password: event.target.value })} /></label>
          <button>Verify</button>
        </form>
      </div>
      {message && <div className="notice">{message}</div>}
      {error && <div className="error">{error}</div>}
      <div className="table">
        {items.map((dialog) => (
          <div className="row" key={dialog.dialog_id}>
            <span>{dialog.title}</span><span>{dialog.kind}</span><span>{dialog.is_enabled ? "Enabled" : "Disabled"}</span>
            <button onClick={() => api.enableChannel(dialog.dialog_id, !dialog.is_enabled).then(refresh)}>Toggle</button>
            <button onClick={() => api.syncMessages(dialog.dialog_id)}>Sync</button>
          </div>
        ))}
      </div>
    </section>
  );
}

export function MessagesPage() {
  const { items, error, refresh, setItems } = useAsyncList<Message>(() => api.messages());
  const [query, setQuery] = useState("");
  async function search() {
    const result = query ? await api.searchMessages(query) : await api.messages();
    return result as Message[];
  }
  return (
    <section>
      <div className="page-heading"><p className="eyebrow">Messages</p><h1>Stored Telegram messages</h1></div>
      <div className="toolbar"><input placeholder="Search messages" value={query} onChange={(event) => setQuery(event.target.value)} /><button onClick={() => search().then(setItems)}>Search</button><button onClick={refresh}>Refresh</button></div>
      {error && <div className="error">{error}</div>}
      <div className="cards">{items.map((item) => <article key={item.id}><strong>{item.sender_name ?? "Unknown"}</strong><p>{item.text}</p><button onClick={() => api.reparse(item.id)}>Parse</button></article>)}</div>
    </section>
  );
}

export function SignalsPage() {
  const { items, error, refresh } = useAsyncList<ParsedSignal>(() => api.signals());
  return (
    <section>
      <div className="page-heading"><p className="eyebrow">Signals</p><h1>Parsed trade signals</h1></div>
      <button onClick={refresh}>Refresh signals</button>
      {error && <div className="error">{error}</div>}
      <div className="table">{items.map((signal) => <div className="row" key={signal.id}><span>{signal.symbol ?? "No symbol"}</span><span>{signal.side ?? "No side"}</span><span>{signal.status}</span><span>{Math.round(signal.confidence * 100)}%</span><button onClick={() => api.executeTest(signal.id)}>Evaluate trade</button></div>)}</div>
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
    <section>
      <div className="page-heading"><p className="eyebrow">MT5</p><h1>Cloud bridge accounts</h1></div>
      <form className="panel" onSubmit={submit}>
        <label>Name<input value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} /></label>
        <label>Provider account ID<input value={form.provider_account_id} onChange={(event) => setForm({ ...form, provider_account_id: event.target.value })} /></label>
        <label>Bridge token<input value={form.token} onChange={(event) => setForm({ ...form, token: event.target.value })} /></label>
        <button>Connect MT5 account</button>
      </form>
      {error && <div className="error">{error}</div>}
      <div className="table">{items.map((account) => <div className="row" key={account.id}><span>{account.name}</span><span>{account.status}</span><span>{account.balance ?? "-"}</span><button onClick={() => api.mt5Status(account.id).then(refresh)}>Health check</button></div>)}</div>
    </section>
  );
}

export function AutomationPage() {
  const { items, error, refresh } = useAsyncList<AutomationRule>(() => api.automationRules());
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
  return (
    <section>
      <div className="page-heading"><p className="eyebrow">Automation</p><h1>Risk and execution rules</h1></div>
      <form className="panel" onSubmit={submit}>
        {Object.entries(form).map(([key, value]) => <label key={key}>{key.replaceAll("_", " ")}<input value={value} onChange={(event) => setForm({ ...form, [key]: event.target.value })} /></label>)}
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

export function AdminPage() {
  const [email, setEmail] = useState("");
  const [result, setResult] = useState("");
  async function createInvite(event: FormEvent) {
    event.preventDefault();
    const invite = await api.createInvite(email) as { code: string };
    setResult(invite.code);
  }
  return (
    <section>
      <div className="page-heading"><p className="eyebrow">Admin</p><h1>Invites and system health</h1></div>
      <form className="panel" onSubmit={createInvite}>
        <label>Email optional<input value={email} onChange={(event) => setEmail(event.target.value)} /></label>
        <button>Create invite</button>
      </form>
      {result && <div className="notice">Invite code: {result}</div>}
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
