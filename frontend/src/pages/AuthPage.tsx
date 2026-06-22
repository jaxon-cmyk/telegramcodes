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
    <div className="auth-page">
      <section className="auth-panel">
        <p className="eyebrow">Invite-only beta</p>
        <h1>Telegram signal monitoring with MT5 automation controls.</h1>
        <p>Connect Telegram, parse signal messages, enforce risk rules, and submit trades through a cloud MT5 bridge.</p>
      </section>
      <form className="auth-form" onSubmit={submit}>
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
    </div>
  );
}
