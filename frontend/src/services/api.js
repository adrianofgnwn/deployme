// Thin API client for the DeployMe backend.
//
// Automatically attaches the Supabase access token (JWT) to every request so
// protected endpoints authenticate without each caller wiring it up. The token
// is read from the live Supabase session, not stored separately, so it stays in
// sync with automatic token refresh.

import { supabase } from "./supabase";

// In dev, Vite proxies nothing by default; the backend runs on :8000. Override
// with VITE_API_BASE_URL if the backend lives elsewhere.
const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

async function authHeader() {
  const {
    data: { session },
  } = await supabase.auth.getSession();
  return session?.access_token
    ? { Authorization: `Bearer ${session.access_token}` }
    : {};
}

/**
 * Make a JSON request to the backend, attaching auth + JSON headers.
 * @param {string} path API path beginning with "/api/...".
 * @param {RequestInit} [options] fetch options; `body` may be a plain object.
 * @returns {Promise<any>} parsed JSON response.
 * @throws {Error} with a user-safe message on non-2xx responses.
 */
export async function apiRequest(path, options = {}) {
  const headers = {
    "Content-Type": "application/json",
    ...(await authHeader()),
    ...(options.headers ?? {}),
  };

  const body =
    options.body && typeof options.body === "object"
      ? JSON.stringify(options.body)
      : options.body;

  const res = await fetch(`${API_BASE_URL}${path}`, { ...options, headers, body });

  if (!res.ok) {
    let message = "Something went wrong. Please try again.";
    try {
      const data = await res.json();
      message = data.detail ?? message;
    } catch {
      // Non-JSON error body — keep the generic message.
    }
    throw new Error(message);
  }

  return res.status === 204 ? null : res.json();
}

export { API_BASE_URL };
