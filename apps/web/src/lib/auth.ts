/**
 * Civitas Authentication & Session Management.
 * 
 * Provides client-side session handling without hardcoded fallback credentials.
 * Authorization is strictly validated on the backend.
 */

export type CivicRole = "citizen" | "triage" | "supervisor" | "reviewer" | "admin";

export interface CivicUser {
  id: string;
  email: string;
  name: string;
  role: CivicRole;
  roleTitle?: string;
  ward?: string;
  avatarInitials?: string;
}

export interface UserSession {
  accessToken: string;
  user: CivicUser;
  expiresAt?: string;
}

const SESSION_STORAGE_KEY = "civitas_session";

// In-memory fallback for SSR and testing environments
let memorySession: UserSession | null = null;

export function getSession(): UserSession | null {
  if (typeof window === "undefined" || typeof localStorage === "undefined") {
    return memorySession;
  }
  try {
    const raw = localStorage.getItem(SESSION_STORAGE_KEY);
    if (!raw) return memorySession;
    const session = JSON.parse(raw) as UserSession;
    if (!session || !session.accessToken) return memorySession;
    return session;
  } catch {
    return memorySession;
  }
}

export function setSession(session: UserSession): void {
  memorySession = session;
  if (typeof window !== "undefined" && typeof localStorage !== "undefined") {
    try {
      localStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(session));
      window.dispatchEvent(new Event("civitas_auth_changed"));
      window.dispatchEvent(new Event("storage"));
    } catch {
      // Ignore storage write errors in restricted environments
    }
  }
}

export function clearSession(): void {
  memorySession = null;
  if (typeof window !== "undefined" && typeof localStorage !== "undefined") {
    try {
      localStorage.removeItem(SESSION_STORAGE_KEY);
      window.dispatchEvent(new Event("civitas_auth_changed"));
      window.dispatchEvent(new Event("storage"));
    } catch {
      // Ignore
    }
  }
}

export function getAuthHeaders(): Record<string, string> {
  const session = getSession();
  const headers: Record<string, string> = {
    Accept: "application/json",
  };
  if (session && session.accessToken) {
    headers.Authorization = `Bearer ${session.accessToken}`;
  }
  return headers;
}

export function isAuthenticated(): boolean {
  return getSession() !== null;
}

export function getCurrentUser(): CivicUser | null {
  const session = getSession();
  return session ? session.user : null;
}

export function hasMinimumRole(required: CivicRole): boolean {
  const user = getCurrentUser();
  if (!user) return false;
  const ranks: Record<CivicRole, number> = {
    citizen: 1,
    triage: 2,
    supervisor: 3,
    reviewer: 4,
    admin: 5,
  };
  return (ranks[user.role] || 1) >= (ranks[required] || 1);
}
