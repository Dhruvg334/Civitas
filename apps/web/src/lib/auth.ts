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
  avatarUrl?: string;
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

export interface SignUpResult {
  user: CivicUser | null;
  confirmationRequired: boolean;
}

export const DEMO_PERSONAS: Record<string, CivicUser> = {
  supervisor: {
    id: "usr-supervisor-01",
    name: "Sarah Chen",
    email: "supervisor.chen@bhubaneswar.gov.in",
    role: "reviewer",
    roleTitle: "Municipal Supervisor · Public Works Dept",
    ward: "Bhubaneswar Municipal Zone 1 (Wards 08, 12, 15)",
    avatarInitials: "SC",
  },
  field: {
    id: "usr-field-01",
    name: "Marcus Vance",
    email: "field.dispatch@waterdept.gov.in",
    role: "triage",
    roleTitle: "Field Crew Dispatch Lead · Water & Drainage",
    ward: "Ward 12 Infrastructure Grid",
    avatarInitials: "MV",
  },
  resident: {
    id: "usr-resident-01",
    name: "Ananya Sharma",
    email: "ananya.resident@civic.local",
    role: "citizen",
    roleTitle: "Citizen Reporter · Ward 12 Resident",
    ward: "Ward 12 · DAV Public School Zone",
    avatarInitials: "AS",
  },
};

export const DEMO_CREDENTIALS: Record<string, { password: string; user: CivicUser }> = {
  "supervisor.chen@bhubaneswar.gov.in": {
    password: "SupervisorPass123!",
    user: DEMO_PERSONAS.supervisor,
  },
  "field.dispatch@waterdept.gov.in": {
    password: "FieldDispatch123!",
    user: DEMO_PERSONAS.field,
  },
  "ananya.resident@civic.local": {
    password: "CitizenPass123!",
    user: DEMO_PERSONAS.resident,
  },
  "demo.resident@civitas.local": {
    password: "CitizenPass123!",
    user: DEMO_PERSONAS.resident,
  },
};

export function userFromSupabaseSession(session: { user?: { id?: string; email?: string; user_metadata?: Record<string, unknown>; app_metadata?: Record<string, unknown> } }): CivicUser {
  const sbUser = session?.user;
  const email = sbUser?.email || "";
  let storedUser: Partial<CivicUser> | null = null;
  if (typeof window !== "undefined") {
    try {
      const stored = localStorage.getItem("civitas_current_user");
      if (stored) storedUser = JSON.parse(stored);
    } catch {
      // ignore
    }
  }
  const displayName =
    storedUser?.name ||
    (typeof sbUser?.user_metadata?.display_name === "string" && sbUser.user_metadata.display_name.trim()) ||
    (typeof sbUser?.user_metadata?.name === "string" && sbUser.user_metadata.name.trim()) ||
    email.split("@")[0] ||
    "Civic User";
  const rawRole = (sbUser?.app_metadata?.role as string) || (sbUser?.user_metadata?.role as string) || "citizen";
  const role: CivicRole = ["citizen", "triage", "supervisor", "reviewer", "admin"].includes(rawRole)
    ? (rawRole as CivicRole)
    : "citizen";
  const avatarUrl =
    storedUser?.avatarUrl ||
    (typeof sbUser?.user_metadata?.avatar_url === "string" && sbUser.user_metadata.avatar_url.trim()) ||
    undefined;
  const ward =
    storedUser?.ward ||
    (typeof sbUser?.user_metadata?.ward === "string" && sbUser.user_metadata.ward.trim()) ||
    undefined;
  const roleTitle =
    storedUser?.roleTitle ||
    (typeof sbUser?.user_metadata?.role_title === "string" && sbUser.user_metadata.role_title.trim()) ||
    getRoleTitle(role);
  const avatarInitials =
    (typeof sbUser?.user_metadata?.avatar_initials === "string" && sbUser.user_metadata.avatar_initials.trim()) ||
    (displayName || "CU").split(/\s+/).map((w) => w[0]).slice(0, 2).join("").toUpperCase() ||
    "CU";

  return {
    id: sbUser?.id || "usr-anon",
    email,
    name: displayName,
    role,
    roleTitle,
    ward,
    avatarInitials,
    avatarUrl,
  };
}

export async function restoreSession(): Promise<UserSession | null> {
  if (memorySession?.accessToken || memorySession?.user) {
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
  let user: CivicUser;
  try {
    user = await verifiedUserFromBackend(data.session.access_token);
  } catch {
    user = userFromSupabaseSession(data.session);
  }
  const restored: UserSession = {
    accessToken: data.session.access_token,
    user,
    expiresAt: data.session.expires_at
      ? new Date(data.session.expires_at * 1000).toISOString()
      : undefined,
  };
  setMemorySession(restored);
  return restored;
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

export async function signUpWithPassword(
  email: string,
  password: string,
  displayName: string
): Promise<SignUpResult> {
  const normalizedEmail = email.trim().toLowerCase();

  // Instant demo persona sign-up
  if (DEMO_CREDENTIALS[normalizedEmail]) {
    const demoUser = DEMO_CREDENTIALS[normalizedEmail].user;
    setMemorySession({ user: demoUser });
    return { user: demoUser, confirmationRequired: false };
  }

  const supabase = getSupabaseClient();
  if (!supabase) {
    if (demoMode()) {
      const demoUser: CivicUser = {
        id: `demo-${Date.now()}`,
        email: normalizedEmail,
        name: displayName.trim() || normalizedEmail.split("@")[0] || "Resident",
        role: "citizen",
        roleTitle: "Citizen Reporter (Demo Mode)",
        ward: "Ward 12 · Bhubaneswar",
        avatarInitials: (displayName.trim() || normalizedEmail).slice(0, 2).toUpperCase(),
      };
      setMemorySession({ user: demoUser });
      return { user: demoUser, confirmationRequired: false };
    }
    throw new Error(
      "Supabase identity provider is not configured. Set NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY."
    );
  }

  const { data, error } = await supabase.auth.signUp({
    email: normalizedEmail,
    password,
    options: {
      data: { display_name: displayName.trim() || undefined },
    },
  });

  if (error) {
    const msg = error.message.toLowerCase();
    if (msg.includes("rate limit") || msg.includes("over_email_send_rate_limit")) {
      throw new Error(
        "Supabase email verification rate limit reached. To sign in immediately, use one of the Demo Personas below or disable 'Confirm email' in your Supabase Auth dashboard."
      );
    }
    throw new Error(error.message || "Unable to create the Civitas account.");
  }

  if (!data.session?.access_token) {
    setMemorySession(null);
    return { user: null, confirmationRequired: true };
  }

  let user: CivicUser;
  try {
    user = await verifiedUserFromBackend(data.session.access_token);
  } catch {
    user = userFromSupabaseSession(data.session);
  }

  setMemorySession({
    accessToken: data.session.access_token,
    user,
    expiresAt: data.session.expires_at
      ? new Date(data.session.expires_at * 1000).toISOString()
      : undefined,
  });
  return { user, confirmationRequired: false };
}

export async function signInWithPassword(email: string, password: string): Promise<CivicUser> {
  const normalizedEmail = email.trim().toLowerCase();

  // 1. Instant check for pre-configured demo credentials
  const demoMatch = DEMO_CREDENTIALS[normalizedEmail];
  if (demoMatch && (password === demoMatch.password || demoMode())) {
    setMemorySession({ user: demoMatch.user });
    return demoMatch.user;
  }

  const supabase = getSupabaseClient();
  if (!supabase) {
    if (demoMode()) {
      const demoUser: CivicUser = {
        id: "demo-citizen-01",
        email: normalizedEmail || "demo.resident@civitas.local",
        name: normalizedEmail ? normalizedEmail.split("@")[0] : "Demo Resident",
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

  const { data, error } = await supabase.auth.signInWithPassword({ email: normalizedEmail, password });
  if (error || !data.session?.access_token) {
    // If Supabase rejected but it was a demo persona attempt
    if (demoMatch) {
      setMemorySession({ user: demoMatch.user });
      return demoMatch.user;
    }
    const msg = (error?.message || "").toLowerCase();
    if (msg.includes("email not confirmed")) {
      throw new Error(
        "Your email address has not been confirmed yet. Please click the confirmation link sent to your inbox, or disable 'Confirm email' in your Supabase Auth dashboard."
      );
    }
    if (msg.includes("rate limit") || msg.includes("over_request_rate_limit")) {
      throw new Error(
        "Too many sign-in attempts. Please wait 60 seconds before trying again, or use one of the Demo Personas below."
      );
    }
    if (msg.includes("invalid login credentials") || msg.includes("invalid credentials")) {
      throw new Error(
        "Invalid email or password. If you have not created an account yet, click 'Create Account' above to register, or use a Demo Persona below."
      );
    }
    throw new Error(error?.message || "Invalid authentication credentials.");
  }

  let user: CivicUser;
  try {
    user = await verifiedUserFromBackend(data.session.access_token);
  } catch {
    user = userFromSupabaseSession(data.session);
  }

  setMemorySession({
    accessToken: data.session.access_token,
    user,
    expiresAt: data.session.expires_at
      ? new Date(data.session.expires_at * 1000).toISOString()
      : undefined,
  });
  return user;
}

export function signInAsPersona(roleKey: "supervisor" | "field" | "resident"): CivicUser {
  const user = DEMO_PERSONAS[roleKey] || DEMO_PERSONAS.resident;
  setMemorySession({ user });
  return user;
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
      let user: CivicUser;
      try {
        user = await verifiedUserFromBackend(session.access_token);
      } catch {
        user = userFromSupabaseSession(session);
      }
      const nextSession: UserSession = {
        accessToken: session.access_token,
        user,
        expiresAt: session.expires_at
          ? new Date(session.expires_at * 1000).toISOString()
          : undefined,
      };
      setMemorySession(nextSession);
      if (active) callback(user);
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

export async function updateUserProfile(updates: Partial<CivicUser>): Promise<CivicUser> {
  const current = memorySession?.user;
  if (!current) {
    throw new Error("No active user session.");
  }
  const name = updates.name !== undefined ? updates.name.trim() : current.name;
  const avatarInitials =
    updates.avatarInitials !== undefined && updates.avatarInitials.trim() !== ""
      ? updates.avatarInitials.trim().slice(0, 2).toUpperCase()
      : current.avatarInitials || (name ? name.slice(0, 2).toUpperCase() : "CU");
  const avatarUrl = updates.avatarUrl !== undefined ? updates.avatarUrl : current.avatarUrl;

  const updatedUser: CivicUser = {
    ...current,
    ...updates,
    name: name || current.name,
    avatarInitials: avatarInitials || (name ? name.slice(0, 2).toUpperCase() : "CU"),
    avatarUrl,
  };

  const updatedSession: UserSession = {
    ...memorySession,
    user: updatedUser,
  };
  setMemorySession(updatedSession);

  if (typeof window !== "undefined") {
    try {
      localStorage.setItem("civitas_current_user", JSON.stringify(updatedUser));
      localStorage.setItem("civitas_onboarding_completed", "true");
      window.dispatchEvent(new Event("storage"));
    } catch {
      // ignore
    }
  }

  const supabase = getSupabaseClient();
  if (supabase) {
    try {
      await supabase.auth.updateUser({
        data: {
          display_name: updatedUser.name,
          ward: updatedUser.ward,
          role_title: updatedUser.roleTitle,
          avatar_initials: updatedUser.avatarInitials,
          avatar_url: updatedUser.avatarUrl || null,
        },
      });
    } catch {
      // ignore
    }
  }

  return updatedUser;
}

export function getCurrentUser(): CivicUser | null {
  return memorySession?.user || null;
}
