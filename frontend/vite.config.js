import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// envDir points one level up so the frontend reads VITE_-prefixed variables
// from the repo-root .env — the same file the backend uses — instead of a
// duplicate frontend/.env. Vite only ever exposes VITE_-prefixed vars to the
// client bundle, so the backend-only secrets in that file stay server-side.
export default defineConfig({
  plugins: [react()],
  envDir: "../",
  server: {
    host: true, // listen on 0.0.0.0 so the Docker container is reachable
    port: 5173,
  },
});
