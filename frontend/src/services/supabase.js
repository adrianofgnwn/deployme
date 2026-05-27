// IMPORTANT: This file uses the ANON KEY ONLY (public, safe for the frontend).
// The anon key is designed to be shipped to browsers — it works together with
// Row Level Security so a user can only ever read/write their own rows.
//
// The Supabase SERVICE ROLE KEY must NEVER appear here, never be imported into
// any frontend module, and never be exposed via a VITE_ variable. It bypasses
// RLS and lives exclusively on the backend (see backend/core/supabase_client.py).

import { createClient } from "@supabase/supabase-js";

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseAnonKey) {
  // Fail loud in development so a misconfigured .env is caught immediately.
  console.error(
    "Missing VITE_SUPABASE_URL or VITE_SUPABASE_ANON_KEY. Copy .env.example to .env and fill them in."
  );
}

export const supabase = createClient(supabaseUrl, supabaseAnonKey, {
  auth: {
    persistSession: true,
    autoRefreshToken: true, // Supabase refreshes the access token automatically
    detectSessionInUrl: true, // needed for magic-link / OAuth callback handling
  },
});
