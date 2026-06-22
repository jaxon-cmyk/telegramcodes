import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/auth": "http://localhost:8000",
      "/admin": "http://localhost:8000",
      "/telegram": "http://localhost:8000",
      "/messages": "http://localhost:8000",
      "/signals": "http://localhost:8000",
      "/mt5": "http://localhost:8000",
      "/automation-rules": "http://localhost:8000",
      "/trade-intents": "http://localhost:8000",
      "/trades": "http://localhost:8000",
      "/invites": "http://localhost:8000"
    }
  }
});
