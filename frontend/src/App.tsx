import { useEffect, useState } from "react";
import type { ReactElement } from "react";
import { Shell } from "./components/Shell";
import { api, clearToken, getToken } from "./services/api";
import { AdminPage, AutomationPage, LogsPage, MessagesPage, MT5Page, OverviewPage, SignalsPage, TelegramPage, TradeIntentsPage, TradesPage } from "./pages/DashboardPages";
import { AuthPage } from "./pages/AuthPage";
import type { User } from "./types/api";

export default function App() {
  const [user, setUser] = useState<User | null>(null);
  const [active, setActive] = useState("overview");
  const [loading, setLoading] = useState(true);

  async function loadUser() {
    if (!getToken()) {
      setLoading(false);
      return;
    }
    try {
      setUser((await api.me()) as User);
    } catch {
      clearToken();
      setUser(null);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadUser();
  }, []);

  if (loading) return <div className="loading">Loading dashboard...</div>;
  if (!user) return <AuthPage onAuthenticated={loadUser} />;

  const pages: Record<string, ReactElement> = {
    overview: <OverviewPage user={user} />,
    telegram: <TelegramPage />,
    messages: <MessagesPage />,
    signals: <SignalsPage />,
    mt5: <MT5Page />,
    automation: <AutomationPage />,
    intents: <TradeIntentsPage />,
    trades: <TradesPage />,
    logs: <LogsPage />,
    admin: <AdminPage />
  };

  return <Shell active={active} onNavigate={setActive}>{pages[active] ?? pages.overview}</Shell>;
}
