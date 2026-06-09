/**
 * Authentication context.
 *
 * Holds the current user, exposes login/logout, and restores the session on
 * load by calling /auth/me/ when a token is present. The Axios interceptor
 * (api/client.js) handles attaching and refreshing tokens.
 */
import { createContext, useContext, useEffect, useState } from "react";
import { tokenStore } from "../api/client";
import * as authApi from "../api/auth";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function restore() {
      if (!tokenStore.getAccess()) {
        setLoading(false);
        return;
      }
      try {
        setUser(await authApi.fetchMe());
      } catch {
        tokenStore.clear();
      } finally {
        setLoading(false);
      }
    }
    restore();
  }, []);

  async function login(username, password) {
    await authApi.login(username, password);
    setUser(await authApi.fetchMe());
  }

  function logout() {
    authApi.logout();
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within an AuthProvider");
  return ctx;
}
