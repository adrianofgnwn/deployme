// Convenience hook for consuming AuthContext. Throws if used outside the
// provider so the mistake surfaces during development rather than as a silent
// null.

import { useContext } from "react";
import { AuthContext } from "../context/AuthContext";

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (ctx === null) {
    throw new Error("useAuth must be used within an <AuthProvider>");
  }
  return ctx;
}
