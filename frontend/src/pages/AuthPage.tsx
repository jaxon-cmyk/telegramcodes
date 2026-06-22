import { FormEvent, useState } from "react";
import { api, setToken } from "../services/api";

export function AuthPage({ onAuthenticated }: { onAuthenticated: () => void }) {
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("admin@example.com");
  const [password, setPassword] = useState("ChangeMe123!");
  const [invite, setInvite] = useState("");
  const [error, setError] = useState("");

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError("");
    try {
      const result = mode === "login" ? await api.login(email, password) : await api.register(email, password, invite);
      setToken(result.access_token);
      onAuthenticated();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Authentication failed");
    }
  }

  return (
    <div className="public-site">
      <header className="public-nav">
        <a className="public-brand" href="#top" aria-label="SignalBridge home">
          <span className="brand-mark">SB</span>
          <span>
            <strong>SignalBridge</strong>
            <small>Telegram to MT5</small>
          </span>
        </a>
        <nav aria-label="Public navigation">
          <a href="#workflow">Workflow</a>
          <a href="#safety">Safety</a>
          <a href="#access">Access</a>
        </nav>
        <a className="nav-cta" href="#login">Sign in</a>
      </header>

      <main id="top">
        <section className="hero-section">
          <div className="hero-copy">
            <p className="eyebrow">Invite-only beta</p>
            <h1>Turn Telegram trading signals into controlled MT5 actions.</h1>
            <p>
              SignalBridge monitors the Telegram channels you already belong to, parses trade signals,
              checks your risk rules, and prepares MT5 trade intents through a cloud bridge built for
              Mac-friendly access.
            </p>
            <div className="hero-actions">
              <a className="primary-link" href="#login">Access dashboard</a>
              <a className="secondary-link" href="#workflow">See how it works</a>
            </div>
            <div className="trust-strip" aria-label="Platform highlights">
              <span>Private channel support</span>
              <span>Rules-first parser</span>
              <span>Cloud MT5 bridge</span>
            </div>
          </div>

          <div className="hero-console" aria-label="SignalBridge dashboard preview">
            <div className="console-bar">
              <span></span><span></span><span></span>
              <strong>Live signal pipeline</strong>
            </div>
            <div className="signal-flow">
              <article>
                <small>Telegram</small>
                <strong>Demo Forex Signals</strong>
                <p>BUY EURUSD ENTRY 1.0720 SL 1.0680 TP1 1.0780</p>
              </article>
              <article>
                <small>Parser</small>
                <strong>86% confidence</strong>
                <p>Symbol, side, entry, stop loss, and take profit normalized.</p>
              </article>
              <article>
                <small>Automation</small>
                <strong>Risk checks passed</strong>
                <p>Allowed symbol, SL required, max lot, and duplicate window verified.</p>
              </article>
              <article>
                <small>MT5 bridge</small>
                <strong>Trade intent ready</strong>
                <p>Order check and order send are routed through the configured provider.</p>
              </article>
            </div>
          </div>
        </section>

        <section className="public-section" id="workflow">
          <div className="section-heading">
            <p className="eyebrow">Workflow</p>
            <h2>Built around the exact trading flow.</h2>
          </div>
          <div className="feature-grid">
            <article>
              <span>01</span>
              <h3>Connect Telegram</h3>
              <p>Users connect their own Telegram account with API ID, API hash, phone code, and optional 2FA.</p>
            </article>
            <article>
              <span>02</span>
              <h3>Choose channels</h3>
              <p>Enable private or public channels and groups that the connected Telegram account can already access.</p>
            </article>
            <article>
              <span>03</span>
              <h3>Parse signals</h3>
              <p>Rules extract symbol, side, entry, SL, TP, lot, risk, confidence, and a parse explanation.</p>
            </article>
            <article>
              <span>04</span>
              <h3>Control MT5 trades</h3>
              <p>Automation rules decide if a validated signal becomes a trade intent for the MT5 cloud bridge.</p>
            </article>
          </div>
        </section>

        <section className="public-section safety-band" id="safety">
          <div>
            <p className="eyebrow">Risk controls</p>
            <h2>Auto trading, but not uncontrolled trading.</h2>
            <p>
              Every trade intent is checked against user rules before provider submission. Blocked signals
              stay visible with the exact reason, so users can audit what happened.
            </p>
          </div>
          <ul className="check-list">
            <li>Allowed symbol list</li>
            <li>Max lot and max risk percent</li>
            <li>Stop-loss required option</li>
            <li>Max trades per day</li>
            <li>Duplicate signal prevention</li>
            <li>Provider failure logging</li>
          </ul>
        </section>

        <section className="public-section access-section" id="access">
          <div>
            <p className="eyebrow">Access</p>
            <h2>Invite-only while the bridge is tested.</h2>
            <p>
              The first version keeps users gated by invite codes, stores Telegram and MT5 credentials
              encrypted, and scopes every dashboard query to the signed-in user.
            </p>
          </div>
          <form className="auth-form" id="login" onSubmit={submit}>
            <h2>{mode === "login" ? "Log in" : "Register with invite"}</h2>
            <label>Email<input value={email} onChange={(event) => setEmail(event.target.value)} /></label>
            <label>Password<input type="password" value={password} onChange={(event) => setPassword(event.target.value)} /></label>
            {mode === "register" && <label>Invite code<input value={invite} onChange={(event) => setInvite(event.target.value)} /></label>}
            {error && <div className="error">{error}</div>}
            <button type="submit">{mode === "login" ? "Log in" : "Create account"}</button>
            <button type="button" className="link-button" onClick={() => setMode(mode === "login" ? "register" : "login")}>
              {mode === "login" ? "Need an invite account?" : "Already have an account?"}
            </button>
          </form>
        </section>
      </main>
    </div>
  );
}
