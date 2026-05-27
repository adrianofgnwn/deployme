// Auth state shared across the app. Wraps Supabase auth so components never
// touch the client directly — they call the helpers exposed here via useAuth().

import { createContext, useEffect, useMemo, useState } from "react";
import { supabase } from "../services/supabase";

export const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [session, setSession] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Load any persisted session on first mount.
    supabase.auth.getSession().then(({ data }) => {
      setSession(data.session);
      setLoading(false);
    });

    // Keep React state in sync with sign-in, sign-out, and token refreshes.
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, newSession) => {
      setSession(newSession);
    });

    return () => subscription.unsubscribe();
  }, []);

  const value = useMemo(
    () => ({
      session,
      user: session?.user ?? null,
      // The access token (JWT) the backend verifies on protected requests.
      accessToken: session?.access_token ?? null,
      isAuthenticated: !!session,
      loading,
      signInWithPassword: (email, password) =>
        supabase.auth.signInWithPassword({ email, password }),
      signUp: (email, password) => supabase.auth.signUp({ email, password }),
      signInWithMagicLink: (email) =>
        supabase.auth.signInWithOtp({ email }),
      signOut: () => supabase.auth.signOut(),
    }),
    [session, loading]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
