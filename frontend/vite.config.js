import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      // Lets the frontend call relative paths like /detect/image in dev,
      // same as it will in prod if served behind the same reverse proxy.
      "/detect": "http://localhost:8000",
      "/track": "http://localhost:8000",
      "/results": "http://localhost:8000",
      "/health": "http://localhost:8000",
      "/config": "http://localhost:8000",
      "/outputs": "http://localhost:8000",
    },
  },
});
