/**
 * Civitas authentication and verified session state.
 *
 * Supabase owns authentication. Civitas API /me owns the application role
 * shown by the frontend. Browser code never manufactures credentials or
 * assigns municipal privileges from client-controlled metadata.
 */

import { getSupabaseClient, isSupabaseConfigured } from "@/lib/supabase/client";

export { isSupabaseConfigured };

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
  accessToken?: string;
  user: CivicUser;
  expiresAt?: string;
}

interface VerifiedPrincipalResponse {
  success: true;
  data: {
    user_id: string;
    email: string;
    role: CivicRole;
    display_name: string;
  };
}

let memorySession: UserSession | null = null;

function apiBaseUrl(): string {
  const raw = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/v1";
  const trimmed = raw.replace(/\/+$/, "");
  return trimmed.endsWith("/api/v1") ? trimmed : `${trimmed}/api/v1`;
}

function demoMode(): boolean {
  return process.env.NEXT_PUBLIC_CIVITAS_DEMO_MODE === "true";
}

async function verifiedUserFromBackend(accessToken: string): Promise<CivicUser> {
  const response = await fetch(`${apiBaseUrl()}/me`, {
    headers: {
      Accept: "application/json",
      Authorization: `Bearer ${accessToken}`,
    },
  });
  if (!response.ok) {
    throw new Error(`Civitas identity verification failed (HTTP ${response.status}).`);
  }
  const payload = (await response.json()) as VerifiedPrincipalResponse;
  if (!payload?.success || !payload.data?.user_id || !payload.data?.role) {
    throw new Error("Civitas identity verification returned an invalid response.");
  }
  const name = payload.data.display_name || payload.data.email.split("@")[0] || "Civic User";
  return {
    id: payload.data.user_id,
    email: payload.data.email,
    name,
    role: payload.data.role,
    roleTitle: getRoleTitle(payload.data.role),
    avatarInitials: name.slice(0, 2).toUpperCase(),
  };
}

export function getMemorySession(): UserSession | null {
  return memorySession;
}

export function setMemorySession(session: UserSession | null): void {
  memorySession = session;
  if (typeof window !== "undefined") {
    window.dispatchEvent(new Event("civitas_auth_changed"));
  }
}

export async function restoreSession(): Promise<UserSession | null> {
  if (memorySession?.accessToken) {
    return memorySession;
  }
  const supabase = getSupabaseClient();
  if (!supabase) {
    return memorySession;
  }
  const { data, error } = await supabase.auth.getSession();
  if (error || !data.session?.access_token) {
    setMemorySession(null);
    return null;
  }
  try {
    const user = await verifiedUserFromBackend(data.session.access_token);
    const restored: UserSession = {
      accessToken: data.session.access_token,
      user,
      expiresAt: data.session.expires_at
        ? new Date(data.session.expires_at * 1000).toISOString()
        : undefined,
    };
    setMemorySession(restored);
    return restored;
  } catch {
    await supabase.auth.signOut();
    setMemorySession(null);
    return null;
  }
}

export async function getAccessToken(): Promise<string | null> {
  if (memorySession?.accessToken) {
    return memorySession.accessToken;
  }
  const restored = await restoreSession();
  return restored?.accessToken || null;
}

export async function getAuthHeadersAsync(): Promise<Record<string, string>> {
  const token = await getAccessToken();
  const headers: Record<string, string> = { Accept: "application/json" };
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  return headers;
}

export function getAuthHeaders(): Record<string, string> {
  const headers: Record<string, string> = { Accept: "application/json" };
  if (memorySession?.accessToken) {
    headers.Authorization = `Bearer ${memorySession.accessToken}`;
  }
  return headers;
}

export interface SignUpResult {
  user: CivicUser | null;
  confirmationRequired: boolean;
}

export async function signUpWithPassword(
  email: string,
  password: string,
  displayName: string
): Promise<SignUpResult> {
  const supabase = getSupabaseClient();
  if (!supabase) {
    throw new Error(
      "Supabase identity provider is not configured. Set NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY."
    );
  }

  const { data, error } = await supabase.auth.signUp({
    email,
    password,
    options: {
      data: { display_name: displayName.trim() || undefined },
    },
  });
  if (error) {
    throw new Error(error.message || "Unable to create the Civitas account.");
  }

  if (!data.session?.access_token) {
    setMemorySession(null);
    return { user: null, confirmationRequired: true };
  }

  try {
    const user = await verifiedUserFromBackend(data.session.access_token);
    setMemorySession({
      accessToken: data.session.access_token,
      user,
      expiresAt: data.session.expires_at
        ? new Date(data.session.expires_at * 1000).toISOString()
        : undefined,
    });
    return { user, confirmationRequired: false };
  } catch (verificationError) {
    await supabase.auth.signOut();
    setMemorySession(null);
    throw verificationError;
  }
}

export async function signInWithPassword(email: string, password: string): Promise<CivicUser> {
  const supabase = getSupabaseClient();
  if (!supabase) {
    if (demoMode()) {
      const demoUser: CivicUser = {
        id: "demo-citizen-01",
        email: email || "demo.resident@civitas.local",
        name: email ? email.split("@")[0] : "Demo Resident",
        role: "citizen",
        roleTitle: "Citizen Reporter (Demo Mode)",
        ward: "Ward 12 · Bhubaneswar",
        avatarInitials: "DR",
      };
      setMemorySession({ user: demoUser });
      return demoUser;
    }
    throw new Error(
      "Supabase identity provider is not configured. Set NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY."
    );
  }

  const { data, error } = await supabase.auth.signInWithPassword({ email, password });
  if (error || !data.session?.access_token) {
    throw new Error(error?.message || "Invalid authentication credentials.");
  }

  try {
    const user = await verifiedUserFromBackend(data.session.access_token);
    setMemorySession({
      accessToken: data.session.access_token,
      user,
      expiresAt: data.session.expires_at
        ? new Date(data.session.expires_at * 1000).toISOString()
        : undefined,
    });
    return user;
  } catch (verificationError) {
    await supabase.auth.signOut();
    setMemorySession(null);
    throw verificationError;
  }
}

export async function signOut(): Promise<void> {
  const supabase = getSupabaseClient();
  if (supabase) {
    await supabase.auth.signOut();
  }
  setMemorySession(null);
}

export function hasMinimumRole(role: CivicRole, required: CivicRole): boolean {
  const ranks: Record<CivicRole, number> = {
    citizen: 1,
    triage: 2,
    supervisor: 3,
    reviewer: 4,
    admin: 5,
  };
  return ranks[role] >= ranks[required];
}

export function getRoleTitle(role: CivicRole): string {
  switch (role) {
    case "admin":
      return "Municipal System Administrator";
    case "reviewer":
      return "Municipal Reviewer";
    case "supervisor":
      return "Municipal Field Supervisor";
    case "triage":
      return "Civic Operations Triage";
    case "citizen":
    default:
      return "Registered Citizen";
  }
}

export function onAuthStateChange(callback: (user: CivicUser | null) => void): () => void {
  if (typeof window === "undefined") {
    return () => {};
  }

  let active = true;
  const supabase = getSupabaseClient();
  const sync = async () => {
    const restored = await restoreSession();
    if (active) callback(restored?.user || memorySession?.user || null);
  };

  void sync();

  let supabaseUnsubscribe: (() => void) | null = null;
  if (supabase) {
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange(async (_event, session) => {
      if (!active) return;
      if (!session?.access_token) {
        setMemorySession(null);
        callback(null);
        return;
      }
      try {
        const user = await verifiedUserFromBackend(session.access_token);
        const nextSession: UserSession = {
          accessToken: session.access_token,
          user,
          expiresAt: session.expires_at
            ? new Date(session.expires_at * 1000).toISOString()
            : undefined,
        };
        setMemorySession(nextSession);
        if (active) callback(user);
      } catch {
        setMemorySession(null);
        if (active) callback(null);
      }
    });
    supabaseUnsubscribe = () => subscription.unsubscribe();
  }

  const handleCustomChange = () => callback(memorySession?.user || null);
  window.addEventListener("civitas_auth_changed", handleCustomChange);

  return () => {
    active = false;
    supabaseUnsubscribe?.();
    window.removeEventListener("civitas_auth_changed", handleCustomChange);
  };
}

// Test helpers.
export function setSession(session: UserSession): void {
  setMemorySession(session);
}

export function clearSession(): void {
  setMemorySession(null);
}

export function getSession(): UserSession | null {
  return memorySession;
}

export function isAuthenticated(): boolean {
  return memorySession !== null;
}

export function getCurrentUser(): CivicUser | null {
  return memorySession?.user || null;
}
