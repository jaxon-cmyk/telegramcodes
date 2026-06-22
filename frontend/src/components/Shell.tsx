import { Activity, Bot, Cable, FileText, HelpCircle, Home, KeyRound, Lock, MessagesSquare, Shield, Sliders, UserCog, WalletCards } from "lucide-react";
import type { ReactNode } from "react";
import type { User } from "../types/api";

type NavItem = {
  id: string;
  label: string;
  icon: ReactNode;
  adminOnly?: boolean;
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
  { id: "setup", label: "Setup Guide", icon: <HelpCircle /> },
  { id: "admin", label: "Admin", icon: <UserCog />, adminOnly: true }
];

export function Shell({ active, onNavigate, user, children }: { active: string; onNavigate: (id: string) => void; user: User; children: ReactNode }) {
  const visibleNav = nav.filter((item) => !item.adminOnly || user.role === "admin");

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <span className="app-logo"><Shield size={22} /></span>
          <div>
            <strong>SignalBridge</strong>
            <span>Telegram to MT5</span>
          </div>
        </div>
        <nav>
          {visibleNav.map((item) => (
            <button key={item.id} className={active === item.id ? "active" : ""} onClick={() => onNavigate(item.id)}>
              {item.icon}
              <span>{item.label}</span>
            </button>
          ))}
        </nav>
        <div className="account-card">
          <span>Signed in</span>
          <strong>{user.email}</strong>
          <small>{user.role === "admin" ? "Administrator" : "Workspace user"}</small>
        </div>
        <div className="source-note">
          <KeyRound size={16} />
          <span>Invite-only beta with encrypted credentials and per-user scoping.</span>
        </div>
      </aside>
      <main className="content">{children}</main>
    </div>
  );
}
