"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import type { User } from "@/lib/types";
import { api } from "@/lib/api";

const TOKEN_KEY = "agentforge_token";
const USER_KEY = "agentforge_user";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  window.localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  window.localStorage.removeItem(TOKEN_KEY);
  window.localStorage.removeItem(USER_KEY);
}

export function getCachedUser(): User | null {
  if (typeof window === "undefined") return null;
  const raw = window.localStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as User;
  } catch {
    return null;
  }
}

export function cacheUser(user: User): void {
  window.localStorage.setItem(USER_KEY, JSON.stringify(user));
}

/**
 * Client-side auth hook. Redirects to /login when no token is present
 * (used by the dashboard layout as a route guard).
 */
export function useAuth(options: { guard?: boolean } = { guard: true }) {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(getCachedUser());
  const [loading, setLoading] = useState(true);
  const [authenticated, setAuthenticated] = useState(false);

  useEffect(() => {
    const token = getToken();
    if (!token) {
      setLoading(false);
      if (options.guard !== false) router.replace("/login");
      return;
    }
    setAuthenticated(true);
    api.auth
      .me()
      .then((me) => {
        setUser(me);
        cacheUser(me);
      })
      .catch(() => {
        // Token invalid/expired — clear and bounce to login.
        clearToken();
        setAuthenticated(false);
        if (options.guard !== false) router.replace("/login");
      })
      .finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const logout = useCallback(() => {
    clearToken();
    router.replace("/login");
  }, [router]);

  return { user, loading, authenticated, logout };
}
