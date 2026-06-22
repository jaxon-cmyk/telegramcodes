import { Activity, Bot, Cable, FileText, Home, KeyRound, Lock, MessagesSquare, Shield, Sliders, UserCog, WalletCards } from "lucide-react";
import type { ReactNode } from "react";

type NavItem = {
  id: string;
  label: string;
  icon: ReactNode;
};

const nav: NavItem[] = [
  { id: "overview", label: "Overview", icon: <Home /> },
  { id: "telegram", label: "Telegram", icon: <MessagesSquare /> },
  { id: "messages", label: "Messages", icon: <FileText /> },
  { id: "signals", label: "Signals", icon: <Bot /> },
  { id: "mt5", label: "MT5 Accounts", icon: <Cable /> },
  { id: "automation", label: "Automation", icon: <Sliders /> },
  { id: "intents", label: "Trade Intents", icon: <Activity /> },
  { id: "trades", label: "Trade History", icon: <WalletCards /> },
  { id: "logs", label: "Execution Logs", icon: <Lock /> },
  { id: "admin", label: "Admin", icon: <UserCog /> }
];

export function Shell({ active, onNavigate, children }: { active: string; onNavigate: (id: string) => void; children: ReactNode }) {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <Shield size={28} />
          <div>
            <strong>SignalBridge</strong>
            <span>Telegram to MT5</span>
          </div>
        </div>
        <nav>
          {nav.map((item) => (
            <button key={item.id} className={active === item.id ? "active" : ""} onClick={() => onNavigate(item.id)}>
              {item.icon}
              <span>{item.label}</span>
            </button>
          ))}
        </nav>
        <div className="source-note">
          <KeyRound size={16} />
          <span>Invite-only beta with encrypted credentials and per-user scoping.</span>
        </div>
      </aside>
      <main className="content">{children}</main>
    </div>
  );
}
