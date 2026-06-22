const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "";
const TOKEN_KEY = "telegram_mt5_token";

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string) {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers);
  headers.set("Content-Type", "application/json");
  const token = getToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const response = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail ?? `Request failed: ${response.status}`);
  }
  return response.json();
}

export const api = {
  login: (email: string, password: string) =>
    request<{ access_token: string }>("/auth/login", { method: "POST", body: JSON.stringify({ email, password }) }),
  register: (email: string, password: string, invite_code: string) =>
    request<{ access_token: string }>("/auth/register", { method: "POST", body: JSON.stringify({ email, password, invite_code }) }),
  me: () => request("/auth/me"),
  createInvite: (email?: string) => request("/invites", { method: "POST", body: JSON.stringify({ email: email || null }) }),
  adminUsers: () => request("/admin/users"),
  updateAdminUser: (id: number, payload: Record<string, unknown>) =>
    request(`/admin/users/${id}`, { method: "PATCH", body: JSON.stringify(payload) }),
  systemHealth: () => request("/admin/system-health"),
  connectTelegram: (payload: Record<string, string>) => request("/telegram/connect", { method: "POST", body: JSON.stringify(payload) }),
  verifyTelegram: (payload: Record<string, string | number>) => request("/telegram/verify", { method: "POST", body: JSON.stringify(payload) }),
  dialogs: () => request("/telegram/dialogs"),
  enableChannel: (dialogId: string, enabled = true) =>
    request(`/telegram/channels/${dialogId}/enable`, { method: "POST", body: JSON.stringify({ enabled }) }),
  syncMessages: (dialogId: string) => request(`/telegram/messages/${dialogId}`),
  searchMessages: (query: string) => request("/telegram/search", { method: "POST", body: JSON.stringify({ query }) }),
  messages: () => request("/messages"),
  signals: () => request("/signals"),
  reparse: (messageId: number) => request(`/signals/${messageId}/reparse`, { method: "POST" }),
  connectMT5: (payload: Record<string, unknown>) => request("/mt5/accounts/connect", { method: "POST", body: JSON.stringify(payload) }),
  mt5Accounts: () => request("/mt5/accounts"),
  mt5Status: (id: number) => request(`/mt5/accounts/${id}/status`),
  mt5Positions: (id: number) => request(`/mt5/accounts/${id}/positions`),
  mt5History: (id: number) => request(`/mt5/accounts/${id}/history`),
  automationRules: () => request("/automation-rules"),
  createAutomationRule: (payload: Record<string, unknown>) =>
    request("/automation-rules", { method: "POST", body: JSON.stringify(payload) }),
  patchAutomationRule: (id: number, payload: Record<string, unknown>) =>
    request(`/automation-rules/${id}`, { method: "PATCH", body: JSON.stringify(payload) }),
  tradeIntents: () => request("/trade-intents"),
  executeTest: (signalId: number) => request(`/trade-intents/${signalId}/execute-test`, { method: "POST" }),
  trades: () => request("/trades"),
  auditLogs: () => request("/audit-logs")
};
