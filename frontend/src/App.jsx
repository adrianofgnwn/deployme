// Phase 0 app shell. Confirms the security foundation is wired end-to-end:
// it pings the backend /api/health endpoint and reflects Supabase auth state.
// The full Chat / Analytics / Optimizer / Tracker pages and router arrive in
// later phases.

import { useEffect, useState } from "react";
import { useAuth } from "./hooks/useAuth";
import { apiRequest } from "./services/api";

function App() {
  const { user, isAuthenticated, loading, signOut } = useAuth();
  const [backend, setBackend] = useState({ state: "checking" });

  useEffect(() => {
    apiRequest("/api/health")
      .then((data) => setBackend({ state: "ok", data }))
      .catch((err) => setBackend({ state: "error", message: err.message }));
  }, []);

  return (
    <main className="min-h-screen flex flex-col items-center justify-center gap-6 p-8">
      <header className="text-center">
        <h1 className="text-4xl font-bold tracking-tight">🚀 DeployMe</h1>
        <p className="text-neutral-400 mt-2">
          Deploy yourself into the job market.
        </p>
      </header>

      <section className="font-mono text-sm space-y-2 rounded-lg border border-neutral-800 bg-neutral-900 p-6 w-full max-w-md">
        <div className="flex justify-between">
          <span className="text-neutral-400">Backend</span>
          <span>
            {backend.state === "checking" && "checking…"}
            {backend.state === "ok" && `✅ ${backend.data.status}`}
            {backend.state === "error" && `❌ ${backend.message}`}
          </span>
        </div>
        <div className="flex justify-between">
          <span className="text-neutral-400">Auth</span>
          <span>
            {loading
              ? "loading…"
              : isAuthenticated
                ? `✅ ${user.email}`
                : "not signed in"}
          </span>
        </div>
      </section>

      {isAuthenticated && (
        <button
          onClick={signOut}
          className="text-sm text-neutral-400 hover:text-neutral-100 underline"
        >
          Sign out
        </button>
      )}
    </main>
  );
}

export default App;
