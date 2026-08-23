"use client";

import { useEffect, useState, useTransition } from "react";
import Link from "next/link";
import { Footer, Nav, Status } from "@/components/site";
import { FlatIcon } from "@/components/flat-icons";
import { restoreSession, setSession, signOut, CivicUser, UserSession, updateUserProfile } from "@/lib/auth";
import { submitWorkflowClarification, fetchMe, isDemoMode } from "@/lib/api";
import { OnboardingPanel, BHUBANESWAR_LOCALITIES, LocalityItem } from "@/components/onboarding-panel";

const DEFAULT_PERSONAS: Record<string, CivicUser> = {
  resident: {
    id: "usr-resident-01",
    name: "Ananya Sharma",
    email: "ananya.resident@civic.local",
    role: "citizen",
    roleTitle: "Citizen Reporter · Ward 12 Resident",
    ward: "Ward 12 · DAV Public School Zone",
    avatarInitials: "AS",
  },
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
    name: "Field Operations",
    email: "field.dispatch@waterdept.gov.in",
    role: "triage",
    roleTitle: "Field Crew Dispatch Lead · Water & Drainage",
    ward: "Ward 12 Infrastructure Grid",
    avatarInitials: "FO",
  },
};

const demoReports = [
  {
    id: "REPORT-103",
    incidentId: "INC-0241",
    title: "High-pressure water main burst beside DAV school gate",
    category: "water_leakage",
    priority: "P1 Urgent",
    status: "WAITING_FOR_REVIEW",
    date: "14 mins ago",
    tone: "warn" as const,
    location: "20.2961° N, 85.8245° E (DAV School Gate)",
    actionNeeded: "Awaiting supervisor authorization for Crew #4 dispatch",
  },
  {
    id: "REPORT-097",
    incidentId: "INC-0238",
    title: "Streetlight cluster power outage at East Gate crossroad",
    category: "streetlight",
    priority: "P3 Low",
    status: "WAITING_FOR_CLARIFICATION",
    date: "2 days ago",
    tone: "warn" as const,
    location: "20.3012° N, 85.8315° E (East Gate Junction)",
    actionNeeded: "Municipal question: Is the lamp post pole physically tilted?",
  },
  {
    id: "REPORT-088",
    incidentId: "INC-0235",
    title: "Sunken asphalt pothole on city hospital bus route",
    category: "pothole",
    priority: "P1 Urgent",
    status: "RESOLVED",
    date: "6 days ago",
    tone: "good" as const,
    location: "20.2885° N, 85.8268° E (Hospital Flyover)",
    actionNeeded: "Resolved: Verified by zero-shot classification & crew sign-off",
  },
];

const GUEST_PERSONA: CivicUser = {
  id: "usr-guest",
  name: "Citizen Resident",
  email: "resident@civic.local",
  role: "citizen",
  roleTitle: "Public Citizen Preview",
  avatarInitials: "CR",
};

export default function Profile() {
  const [user, setUser] = useState<CivicUser>(GUEST_PERSONA);
  const [isGuest, setIsGuest] = useState<boolean>(true);
  const [activeTab, setActiveTab] = useState<"overview" | "reports" | "ward" | "settings">("overview");
  const [clarificationReply, setClarificationReply] = useState<string>("");
  const [clarificationSent, setClarificationSent] = useState<boolean>(false);
  const [clarificationError, setClarificationError] = useState<string | null>(null);
  const [savedNotice, setSavedNotice] = useState<string>("");
  const [demoModeActive] = useState<boolean>(() => isDemoMode());
  const [showOnboarding, setShowOnboarding] = useState<boolean>(false);
  const [showEditModal, setShowEditModal] = useState<boolean>(false);
  const [editName, setEditName] = useState<string>("");
  const [editAvatarInitials, setEditAvatarInitials] = useState<string>("");
  const [editAvatarUrl, setEditAvatarUrl] = useState<string>("");
  const [editWard, setEditWard] = useState<string>("");
  const [editRoleTitle, setEditRoleTitle] = useState<string>("");
  const [isSavingProfile, setIsSavingProfile] = useState<boolean>(false);
  const [, startTransition] = useTransition();

  useEffect(() => {
    if (typeof window !== "undefined") {
      const params = new URLSearchParams(window.location.search);
      if (params.get("onboarding") === "true") {
        setShowOnboarding(true);
      }
    }
  }, []);

  useEffect(() => {
    const syncUser = async () => {
      const session = await restoreSession();
      if (session && session.user) {
        let finalUser = session.user;
        if (typeof window !== "undefined") {
          const stored = localStorage.getItem("civitas_current_user");
          if (stored) {
            try {
              const parsed = JSON.parse(stored);
              finalUser = { ...finalUser, ...parsed };
            } catch {
              // ignore
            }
          }
        }
        startTransition(() => {
          setUser(finalUser);
          setIsGuest(false);
        });
        try {
          const verified = await fetchMe();
          if (verified) {
            startTransition(() => {
              setUser((prev) => ({
                ...prev,
                id: verified.user_id,
                email: verified.email,
                role: verified.role as CivicUser["role"],
                name: verified.display_name || prev.name,
              }));
            });
          }
        } catch {
          // Keep active session user
        }
      } else {
        startTransition(() => {
          setUser(GUEST_PERSONA);
          setIsGuest(true);
        });
      }
    };
    syncUser();
    window.addEventListener("storage", syncUser);
    window.addEventListener("civitas_auth_changed", syncUser);
    return () => {
      window.removeEventListener("storage", syncUser);
      window.removeEventListener("civitas_auth_changed", syncUser);
    };
  }, []);

  const openEditModal = () => {
    setEditName(user.name);
    setEditAvatarInitials(user.avatarInitials || (user.name ? user.name.slice(0, 2).toUpperCase() : "CU"));
    setEditAvatarUrl(user.avatarUrl || "");
    setEditWard(user.ward || BHUBANESWAR_LOCALITIES[0].name);
    setEditRoleTitle(user.roleTitle || "Registered Citizen");
    setShowEditModal(true);
  };

  const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (!file.type.startsWith("image/")) {
      alert("Please select a valid image file (PNG, JPG, WebP).");
      return;
    }
    const reader = new FileReader();
    reader.onload = () => {
      if (typeof reader.result === "string") {
        setEditAvatarUrl(reader.result);
      }
    };
    reader.readAsDataURL(file);
  };

  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSavingProfile(true);
    try {
      const finalName = editName.trim() || user.name;
      const finalInitials = editAvatarInitials.trim().slice(0, 2).toUpperCase() || finalName.slice(0, 2).toUpperCase();
      const updated = await updateUserProfile({
        name: finalName,
        avatarInitials: finalInitials,
        avatarUrl: editAvatarUrl || undefined,
        ward: editWard.trim() || user.ward,
        roleTitle: editRoleTitle.trim() || user.roleTitle,
      });
      startTransition(() => {
        setUser(updated);
      });
      setShowEditModal(false);
      setSavedNotice(`Profile updated successfully for ${updated.name}.`);
      setTimeout(() => setSavedNotice(""), 4000);
    } catch (err) {
      setSavedNotice(`Failed to update profile: ${err instanceof Error ? err.message : "Save failed"}`);
    } finally {
      setIsSavingProfile(false);
    }
  };

  const handleSwitchPersona = (roleKey: "resident" | "supervisor" | "field") => {
    if (!demoModeActive) return;
    const selected = DEFAULT_PERSONAS[roleKey];
    const session: UserSession = {
      user: selected,
    };
    setSession(session);
    setUser(selected);
    setIsGuest(false);
    setSavedNotice(`Switched demo preview to ${selected.name} (${selected.roleTitle})`);
    setTimeout(() => setSavedNotice(""), 4000);
  };

  const handleSignOut = async () => {
    await signOut();
    setUser(GUEST_PERSONA);
    setIsGuest(true);
    setSavedNotice("Signed out. Viewing public resident profile.");
    setTimeout(() => setSavedNotice(""), 4000);
  };

  const handleSendClarification = async (e: React.FormEvent) => {
    e.preventDefault();
    setClarificationError(null);
    try {
      if (demoModeActive) {
        await submitWorkflowClarification("wf-demo-light-0238", {
          q1: clarificationReply || "Lamp post is standing upright, but bulb housing is broken.",
        });
      }
      setClarificationSent(true);
      setSavedNotice("Clarification response submitted to municipal dispatch.");
      setTimeout(() => {
        setClarificationSent(false);
        setSavedNotice("");
      }, 5000);
    } catch (err) {
      setClarificationError(err instanceof Error ? err.message : "Failed to submit clarification response.");
      setClarificationSent(false);
    }
  };

  return (
    <>
      <Nav />
      <main className="profile-main-shell">
        {/* TOP NOTICE ALERT */}
        {savedNotice && (
          <div className="session-notice-banner" role="status">
            {savedNotice}
          </div>
        )}

        {/* ONBOARDING MODAL POPUP */}
        {showOnboarding && (
          <OnboardingPanel
            onClose={() => setShowOnboarding(false)}
            initialEmail={user.email}
            initialName={user.name}
          />
        )}

        {/* EDIT PROFILE MODAL */}
        {showEditModal && (
          <div className="edit-profile-modal-backdrop" role="dialog" aria-modal="true">
            <div className="edit-profile-modal-card">
              <div className="modal-header-row">
                <div>
                  <span className="profile-kicker">IDENTITY CONFIGURATION</span>
                  <h2 style={{ margin: "4px 0 0", fontFamily: "Georgia, serif", fontSize: "1.6rem" }}>
                    Edit Civic Profile
                  </h2>
                </div>
                <button
                  type="button"
                  className="modal-close-btn"
                  onClick={() => setShowEditModal(false)}
                  aria-label="Close modal"
                >
                  <FlatIcon name="cross" size={14} />
                </button>
              </div>

              <form onSubmit={handleSaveProfile} className="edit-profile-form">
                <div className="edit-avatar-preview-row" style={{ display: "flex", gap: "16px", alignItems: "center", marginBottom: "16px" }}>
                  <div className="preview-avatar-box" style={{ width: "64px", height: "64px", borderRadius: "50%", border: "2px solid #172019", background: "#0f5f4f", color: "#ffffff", display: "grid", placeItems: "center", fontSize: "1.5rem", fontWeight: 700, overflow: "hidden", flexShrink: 0 }}>
                    {editAvatarUrl ? (
                      <img src={editAvatarUrl} alt="Avatar Preview" style={{ width: "100%", height: "100%", objectFit: "cover" }} />
                    ) : (
                      <span>{editAvatarInitials || (editName ? editName.slice(0, 2).toUpperCase() : "CU")}</span>
                    )}
                  </div>
                  <div>
                    <b>Profile Photo & Avatar Initials</b>
                    <div style={{ display: "flex", gap: "8px", alignItems: "center", marginTop: "6px", flexWrap: "wrap" }}>
                      <label className="button secondary small" style={{ cursor: "pointer", display: "inline-flex", alignItems: "center", gap: "4px", fontSize: "0.75rem" }}>
                        <FlatIcon name="camera" size={13} />
                        <span>Upload Photo</span>
                        <input
                          type="file"
                          accept="image/png,image/jpeg,image/webp"
                          style={{ display: "none" }}
                          onChange={handleImageUpload}
                        />
                      </label>
                      {editAvatarUrl && (
                        <button
                          type="button"
                          className="outline small"
                          onClick={() => setEditAvatarUrl("")}
                          style={{ color: "#991b1b", fontSize: "0.75rem" }}
                        >
                          Remove Photo
                        </button>
                      )}
                    </div>
                  </div>
                </div>

                <div className="edit-field-group">
                  <label className="edit-field-label" htmlFor="edit-profile-name">
                    Display Name / Full Name
                  </label>
                  <input
                    id="edit-profile-name"
                    type="text"
                    required
                    value={editName}
                    onChange={(e) => setEditName(e.target.value)}
                    placeholder="e.g. Alex Morgan"
                    className="modal-text-input"
                  />
                </div>

                <div className="edit-field-group">
                  <label className="edit-field-label" htmlFor="edit-avatar-initials">
                    Avatar Initials (1–2 letters, shown when no photo uploaded)
                  </label>
                  <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
                    <input
                      id="edit-avatar-initials"
                      type="text"
                      maxLength={2}
                      value={editAvatarInitials}
                      onChange={(e) => setEditAvatarInitials(e.target.value.toUpperCase())}
                      placeholder="e.g. AM"
                      className="modal-text-input"
                      style={{ width: "90px", textTransform: "uppercase", fontWeight: 800, textAlign: "center" }}
                    />
                    <button
                      type="button"
                      className="outline small"
                      onClick={() => setEditAvatarInitials(editName ? editName.trim().slice(0, 2).toUpperCase() : "CU")}
                      title="Derive 2-letter initials from display name"
                      style={{ fontSize: "0.75rem" }}
                    >
                      Auto from Name
                    </button>
                  </div>
                </div>

                <div className="edit-field-group">
                  <label className="edit-field-label" htmlFor="edit-profile-ward">
                    Registered Bhubaneswar Ward / Locality
                  </label>
                  <select
                    id="edit-profile-ward"
                    value={editWard}
                    onChange={(e) => setEditWard(e.target.value)}
                    className="modal-text-input"
                  >
                    {BHUBANESWAR_LOCALITIES.map((loc: LocalityItem) => (
                      <option key={loc.id} value={loc.id}>
                        {loc.name} ({loc.zone})
                      </option>
                    ))}
                  </select>
                </div>

                <div className="edit-field-group">
                  <label className="edit-field-label" htmlFor="edit-role-title">
                    Role Title / Affiliation Description
                  </label>
                  <input
                    id="edit-role-title"
                    type="text"
                    value={editRoleTitle}
                    onChange={(e) => setEditRoleTitle(e.target.value)}
                    placeholder="e.g. Citizen Reporter · Ward 12 Resident"
                    className="modal-text-input"
                  />
                </div>

                <div className="modal-actions-footer" style={{ marginTop: "24px", display: "flex", justifyContent: "flex-end", gap: "10px" }}>
                  <button
                    type="button"
                    className="outline"
                    onClick={() => setShowEditModal(false)}
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="button large"
                    disabled={isSavingProfile}
                  >
                    {isSavingProfile ? "Saving..." : "Save Profile Changes →"}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* PROFILE HEADER CARD */}
        <section className="profile-hero-card">
          <div
            className="profile-avatar-box"
            onClick={!isGuest ? openEditModal : undefined}
            style={{ cursor: !isGuest ? "pointer" : "default", overflow: "hidden" }}
            title={!isGuest ? "Click to edit avatar photo or display name" : undefined}
          >
            {user.avatarUrl ? (
              <img
                src={user.avatarUrl}
                alt={user.name}
                style={{ width: "100%", height: "100%", objectFit: "cover" }}
              />
            ) : (
              <span>{user.avatarInitials || (user.name ? user.name.slice(0, 2).toUpperCase() : "CU")}</span>
            )}
            {!isGuest && <small className="edit-avatar-hint">Edit</small>}
          </div>

          <div className="profile-hero-info">
            <div className="hero-kicker-row">
              <span className="profile-kicker">CIVIC IDENTITY & PROFILE</span>
              <span className={`role-badge ${user.role}`}>
                {isGuest ? "PUBLIC GUEST" : user.role.toUpperCase()}
              </span>
            </div>

            <h1 className="profile-name-heading">{user.name}</h1>
            <p className="profile-role-sub">{user.roleTitle}</p>
            <p className="profile-ward-text" style={{ display: "flex", alignItems: "center", gap: "4px" }}>
              <FlatIcon name="pin" size={13} color="#0f5f4f" />
              <span>Profile Area: <b>{user.ward || "Not provided"}</b></span>
            </p>

            {isGuest && (
              <div className="guest-banner-row">
                <Status tone="warn">SIGNED_OUT_PREVIEW</Status>
                <Link className="button small" href="/sign-in">
                  Sign in or create account
                </Link>
              </div>
            )}

            {demoModeActive ? (
              <div className="profile-header-actions">
                <span className="persona-switcher-kicker">
                  ROLE PREVIEW (DEMO): <small style={{ fontWeight: "normal", color: "#687067" }}>(Switch view to inspect resident or supervisor experience)</small>
                </span>
                <div className="persona-pill-group">
                  <button
                    type="button"
                    className={`persona-pill ${user.role === "citizen" ? "active" : ""}`}
                    onClick={() => handleSwitchPersona("resident")}
                  >
                    <FlatIcon name="user" size={12} /> Resident (Ananya)
                  </button>
                  <button
                    type="button"
                    className={`persona-pill ${user.role === "reviewer" || (user.role as string) === "supervisor" ? "active" : ""}`}
                    onClick={() => handleSwitchPersona("supervisor")}
                  >
                    <FlatIcon name="shield" size={12} /> Supervisor (Sarah)
                  </button>
                  <button
                    type="button"
                    className={`persona-pill ${user.role === "triage" ? "active" : ""}`}
                    onClick={() => handleSwitchPersona("field")}
                  >
                    <FlatIcon name="zap" size={12} /> Field Lead (Marcus)
                  </button>
                  {!isGuest && (
                    <button
                      type="button"
                      className="persona-pill signout-pill"
                      onClick={handleSignOut}
                    >
                      Sign Out
                    </button>
                  )}
                </div>
              </div>
            ) : !isGuest ? (
              <div className="profile-header-actions" style={{ display: "flex", gap: "10px", flexWrap: "wrap", marginTop: "16px" }}>
                <button
                  type="button"
                  className="button small"
                  onClick={openEditModal}
                  style={{ display: "inline-flex", alignItems: "center", gap: "6px" }}
                >
                  <FlatIcon name="edit" size={13} /> Edit Profile
                </button>
                <button
                  type="button"
                  className="outline small"
                  onClick={() => setShowOnboarding(true)}
                  style={{ display: "inline-flex", alignItems: "center", gap: "6px" }}
                >
                  <FlatIcon name="compass" size={13} /> Onboarding Setup Wizard
                </button>
                <button
                  type="button"
                  className="outline small"
                  onClick={handleSignOut}
                  style={{ borderColor: "#b91c1c", color: "#b91c1c" }}
                >
                  Sign Out of Session
                </button>
              </div>
            ) : null}
          </div>
        </section>

        {/* STATS TILES */}
        <section className="profile-stats-ribbon">
          {demoModeActive ? (
            <>
              <div className="stat-tile">
                <span className="stat-label">REPORTS TRACKED (DEMO)</span>
                <b className="stat-num">03 Verified</b>
                <small>Active in PostGIS Ward 12</small>
              </div>
              <div className="stat-tile">
                <span className="stat-label">ACTION REQUIRED (DEMO)</span>
                <b className="stat-num alert-num">01 Clarification</b>
                <small>Response needed on REPORT-097</small>
              </div>
              <div className="stat-tile">
                <span className="stat-label">DISPATCHED CREWS (DEMO)</span>
                <b className="stat-num">02 Work Orders</b>
                <small>Public Works & Water Dept</small>
              </div>
              <div className="stat-tile">
                <span className="stat-label">RESOLUTION AUDIT (DEMO)</span>
                <b className="stat-num good-num">Verified</b>
                <small>CLIP CV before/after image match</small>
              </div>
            </>
          ) : (
            <>
              <div className="stat-tile">
                <span className="stat-label">ACCOUNT STATUS</span>
                <b className="stat-num good-num">{isGuest ? "Guest Preview" : "Authenticated"}</b>
                <small>{isGuest ? "Sign in to track reports" : "Identity verified by Civitas API"}</small>
              </div>
              <div className="stat-tile">
                <span className="stat-label">REPORT ACTIVITY</span>
                <b className="stat-num">Not loaded</b>
                <small>User-specific report history is shown when available from the API.</small>
              </div>
              <div className="stat-tile">
                <span className="stat-label">CLARIFICATIONS</span>
                <b className="stat-num">Not loaded</b>
                <small>No clarification count is inferred client-side.</small>
              </div>
              <div className="stat-tile">
                <span className="stat-label">AUTHORIZATION ROLE</span>
                <b className="stat-num good-num">{isGuest ? "Public" : user.role}</b>
                <small>Backend-verified role</small>
              </div>
            </>
          )}
        </section>

        {/* TAB SWITCHER */}
        <nav className="profile-tabs-nav" aria-label="Profile navigation">
          <button
            className={`tab-nav-btn ${activeTab === "overview" ? "active" : ""}`}
            onClick={() => setActiveTab("overview")}
          >
            <FlatIcon name="overview" size={14} />
            <span>Activity Overview</span>
          </button>
          <button
            className={`tab-nav-btn ${activeTab === "reports" ? "active" : ""}`}
            onClick={() => setActiveTab("reports")}
          >
            <FlatIcon name="doc" size={14} />
            <span>Submitted Reports {demoModeActive ? `(${demoReports.length} Demo)` : "(0)"}</span>
          </button>
          <button
            className={`tab-nav-btn ${activeTab === "ward" ? "active" : ""}`}
            onClick={() => setActiveTab("ward")}
          >
            <FlatIcon name="map" size={14} />
            <span>PostGIS Ward Boundaries</span>
          </button>
          <button
            className={`tab-nav-btn ${activeTab === "settings" ? "active" : ""}`}
            onClick={() => setActiveTab("settings")}
          >
            <FlatIcon name="shield" size={14} />
            <span>Account & Notifications</span>
          </button>
        </nav>

        {/* TAB CONTENT */}
        <div className="profile-tab-body">
          {/* TAB 1: OVERVIEW */}
          {activeTab === "overview" && (
            <div className="overview-tab-content">
              {/* CLARIFICATION CARD (DEMO OR ACTIVE) */}
              {demoModeActive ? (
                <div className="clarification-callout-card">
                  <div className="callout-header">
                    <div className="callout-title-row">
                      <FlatIcon name="alert" size={18} color="#b45309" />
                      <b>Pending Field Question for REPORT-097 (Demo Scenario · East Gate Streetlight)</b>
                    </div>
                    <Status tone="warn">WAITING_FOR_CLARIFICATION</Status>
                  </div>
                  <p className="callout-body">
                    Municipal electrical team asks: <i>&quot;Is the luminaire lamp post visibly tilted, or is the bulb intact with no power?&quot;</i>
                  </p>

                  {clarificationSent ? (
                    <div className="clarification-success">
                      ✓ Thank you! Your response was attached to REPORT-097 and routed to Electrical Dispatch.
                    </div>
                  ) : (
                    <form onSubmit={handleSendClarification} className="clarification-form">
                      {clarificationError && (
                        <div className="clarification-error-box" role="alert" style={{ display: "flex", alignItems: "center", gap: "6px", background: "#fee2e2", border: "1px solid #f87171", padding: "8px 12px", borderRadius: "6px", color: "#991b1b", marginBottom: "8px", fontSize: "0.875rem" }}>
                          <FlatIcon name="alert" size={14} color="#991b1b" />
                          <span>{clarificationError}</span>
                        </div>
                      )}
                      <input
                        type="text"
                        placeholder="e.g. The pole is straight, but all 3 lights in the cluster are completely dark."
                        value={clarificationReply}
                        onChange={(e) => setClarificationReply(e.target.value)}
                        required
                        className="clarification-input"
                      />
                      <button type="submit" className="button small">
                        {clarificationError ? "Retry Sending Reply →" : "Send Reply to Field Crew →"}
                      </button>
                    </form>
                  )}
                </div>
              ) : null}

              {/* RECENT REPORTS SECTION */}
              <div className="recent-reports-header">
                <h3>{demoModeActive ? "Active Ward 12 Civic Reports (Demo Showcase)" : "Your Active Civic Reports"}</h3>
                <Link href="/workspace" className="workspace-link">
                  Open in Workspace Command Center →
                </Link>
              </div>

              {demoModeActive ? (
                <div className="reports-dossier-list">
                  {demoReports.map((rpt) => (
                    <article key={rpt.id} className="report-row-card">
                      <div className="rpt-id-col">
                        <span className="rpt-id-tag">{rpt.id}</span>
                        <small className="linked-inc">Grouped in {rpt.incidentId}</small>
                      </div>

                      <div className="rpt-info-col">
                        <b className="rpt-title">{rpt.title}</b>
                        <p className="rpt-loc" style={{ display: "flex", alignItems: "center", gap: "4px" }}>
                          <FlatIcon name="pin" size={12} color="#0f5f4f" /> {rpt.location}
                        </p>
                        <small className="rpt-action">{rpt.actionNeeded}</small>
                      </div>

                      <div className="rpt-status-col">
                        <Status tone={rpt.tone}>{rpt.status}</Status>
                        <span className="rpt-date">{rpt.date}</span>
                      </div>

                      <div className="rpt-action-col">
                        <Link href={`/incidents/${rpt.incidentId}`} className="outline small">
                          Inspect Dossier
                        </Link>
                      </div>
                    </article>
                  ))}
                </div>
              ) : (
                <div className="empty-reports-panel" style={{ border: "1px solid #172019", background: "#fbf9f4", padding: "32px", borderRadius: "6px", textAlign: "center" }}>
                  <p style={{ margin: "0 0 16px", color: "#555e54", fontSize: "0.95rem" }}>
                    No citizen reports filed under this account yet. Reports you submit will appear here with live resolution status and dispatch tracking.
                  </p>
                  <Link href="/report" className="button large">
                    Submit New Civic Report →
                  </Link>
                </div>
              )}
            </div>
          )}

          {/* TAB 2: REPORTS FULL TIMELINE */}
          {activeTab === "reports" && (
            <div className="reports-timeline-content">
              <div className="timeline-header">
                <h2>{demoModeActive ? "Submitted Reports & Resolution Trace (Demo Data)" : "Submitted Reports & Audit History"}</h2>
                <p>Track full auditability: official records preserve original resident photos and timeline entries.</p>
              </div>

              {demoModeActive ? (
                <div className="timeline-list">
                  {demoReports.map((rpt, idx) => (
                    <div key={rpt.id} className="timeline-item">
                      <div className="timeline-marker">
                        <span>0{idx + 1}</span>
                      </div>
                      <div className="timeline-card">
                        <div className="timeline-card-top">
                          <div>
                            <span className="timeline-ref">{rpt.id} · {rpt.priority}</span>
                            <h3>{rpt.title}</h3>
                          </div>
                          <Status tone={rpt.tone}>{rpt.status}</Status>
                        </div>
                        <p className="timeline-meta" style={{ display: "flex", alignItems: "center", gap: "4px" }}>
                          <FlatIcon name="pin" size={12} color="#0f5f4f" /> Coordinates: {rpt.location}
                        </p>
                        <p className="timeline-detail">{rpt.actionNeeded}</p>
                        <div className="timeline-actions">
                          <Link href={`/incidents/${rpt.incidentId}`} className="button small">
                            Open Incident Dossier →
                          </Link>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="empty-timeline-box" style={{ border: "1px solid #172019", background: "#fbf9f4", padding: "36px", borderRadius: "6px", textAlign: "center" }}>
                  <p style={{ margin: "0 0 16px", color: "#555e54" }}>
                    You have not submitted any reports yet. Once submitted, each report receives an official municipal tracking reference and verification audit log.
                  </p>
                  <Link href="/report" className="button large">
                    Report an Issue →
                  </Link>
                </div>
              )}
            </div>
          )}

          {/* TAB 3: WARD BOUNDARIES */}
          {activeTab === "ward" && (
            <div className="ward-boundaries-content">
              <h2>Municipal Geofenced Boundaries</h2>
              <p>Your registered locality helps prevent duplicate reports and ensures faster response times.</p>

              {demoModeActive ? (
                <div className="ward-cards-grid">
                  <div className="ward-select-card active">
                    <div className="ward-card-header">
                      <FlatIcon name="map" size={16} color="#0f5f4f" />
                      <b>Ward 12 · DAV Public School Zone (Demo)</b>
                    </div>
                    <p>Seeded demo zone used to illustrate spatial subscriptions and landmark buffers.</p>
                    <span className="geofence-status">Active ward zone</span>
                  </div>
                </div>
              ) : (
                <div className="empty-reports-panel" style={{ border: "1px solid #172019", background: "#fbf9f4", padding: "32px", borderRadius: "6px" }}>
                  <p style={{ margin: 0, color: "#555e54" }}>No user-specific municipal geofence is available from the current profile API.</p>
                </div>
              )}
            </div>
          )}

          {/* TAB 4: SETTINGS & NOTIFICATIONS */}
          {activeTab === "settings" && (
            <div className="settings-content">
              <h2>Account Identity & Notification Preferences</h2>
              <p>Manage your verified contact details and automated dispatch alerts.</p>

              <div className="settings-box">
                <div className="settings-row">
                  <div>
                    <b>Civic Identity & Profile Customization</b>
                    <p>Change your display name, avatar initials, and primary registered Bhubaneswar ward.</p>
                  </div>
                  <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
                    {!isGuest && (
                      <button
                        type="button"
                        className="button small"
                        onClick={openEditModal}
                        style={{ display: "inline-flex", alignItems: "center", gap: "6px" }}
                      >
                        <FlatIcon name="edit" size={13} /> Edit Profile Details
                      </button>
                    )}
                    <button
                      type="button"
                      className="outline small"
                      onClick={() => setShowOnboarding(true)}
                      style={{ display: "inline-flex", alignItems: "center", gap: "6px" }}
                    >
                      <FlatIcon name="compass" size={13} /> Launch Setup Wizard
                    </button>
                  </div>
                </div>

                <div className="settings-row">
                  <div>
                    <b>Active Account Email</b>
                    <p>{user.email}</p>
                  </div>
                  <span className="verified-pill" style={{ display: "inline-flex", alignItems: "center", gap: "4px" }}>
                    <FlatIcon name="check" size={11} color="#0f5f4f" /> Verified Session
                  </span>
                </div>

                <div className="settings-row">
                  <div>
                    <b>Registered Ward / Neighborhood</b>
                    <p>{user.ward || "Ward 12 · Nayapalli / Unit 8"}</p>
                  </div>
                  <span className="verified-pill" style={{ display: "inline-flex", alignItems: "center", gap: "4px" }}>
                    <FlatIcon name="pin" size={11} color="#0f5f4f" /> Geofenced
                  </span>
                </div>

                <div className="settings-row">
                  <div>
                    <b>PostGIS Infrastructure Alerts</b>
                    <p>Receive notifications when civic hazards occur within 500m of your registered ward.</p>
                  </div>
                  <input type="checkbox" defaultChecked className="settings-checkbox" />
                </div>

                <div className="settings-row">
                  <div>
                    <b>Field Clarification Push Requests</b>
                    <p>Allow municipal supervisors to request single-question photo clarifications.</p>
                  </div>
                  <input type="checkbox" defaultChecked className="settings-checkbox" />
                </div>

                <div className="settings-row">
                  <div>
                    <b>Supervisor Review Clearances</b>
                    <p>Enable work-order dispatch authorizations (Supervisor persona only).</p>
                  </div>
                  <input
                    type="checkbox"
                    checked={user.role === "supervisor"}
                    disabled
                    className="settings-checkbox"
                  />
                </div>

                <div className="settings-row">
                  <div>
                    <b>Account Security & Credentials</b>
                    <p>Update your password or configure two-factor authentication recovery codes.</p>
                  </div>
                  <Link href="/reset-password" className="outline small reset-pw-link">
                    Reset Password →
                  </Link>
                </div>
              </div>
            </div>
          )}
        </div>
      </main>
      <Footer />

      <style jsx>{`
        .profile-main-shell {
          width: min(calc(100% - 40px), 1140px);
          margin: 36px auto 100px;
        }
        .session-notice-banner {
          padding: 12px 16px;
          background: #dce8dd;
          border: 1px solid #0f5f4f;
          color: #0f5f4f;
          font-size: 0.82rem;
          font-weight: 800;
          border-radius: 4px;
          margin-bottom: 24px;
        }
        .edit-profile-modal-backdrop {
          position: fixed;
          inset: 0;
          z-index: 100;
          display: grid;
          place-items: center;
          padding: 20px;
          background: rgba(23, 32, 25, 0.55);
          backdrop-filter: blur(6px);
        }
        .edit-profile-modal-card {
          position: relative;
          width: min(100%, 540px);
          max-height: calc(100vh - 40px);
          overflow-y: auto;
          padding: 32px;
          background: #ffffff;
          border: 2px solid #172019;
          box-shadow: 8px 8px 0 #172019;
          border-radius: 8px;
        }
        .modal-header-row {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          margin-bottom: 20px;
          padding-bottom: 14px;
          border-bottom: 1px solid #e2ded4;
        }
        .modal-close-btn {
          width: 32px;
          height: 32px;
          border: 1px solid #172019;
          background: #fbf9f4;
          display: grid;
          place-items: center;
          font-size: 1rem;
          cursor: pointer;
          border-radius: 4px;
        }
        .modal-close-btn:hover {
          background: #172019;
          color: #ffffff;
        }
        .edit-avatar-preview-row {
          display: flex;
          align-items: center;
          gap: 16px;
          padding: 14px 16px;
          background: #fbf9f4;
          border: 1px solid #172019;
          border-radius: 6px;
          margin-bottom: 20px;
        }
        .preview-avatar-box {
          width: 52px;
          height: 52px;
          border-radius: 50%;
          background: #0f5f4f;
          color: #ffffff;
          border: 1.5px solid #172019;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 1.25rem;
          font-weight: 850;
          font-family: Georgia, serif;
          flex-shrink: 0;
          box-shadow: 2px 2px 0 #172019;
        }
        .edit-field-group {
          display: flex;
          flex-direction: column;
          gap: 6px;
          margin-bottom: 16px;
        }
        .edit-field-label {
          font-size: 0.76rem;
          font-weight: 800;
          color: #172019;
        }
        .modal-text-input {
          padding: 10px 12px;
          border: 1.5px solid #172019;
          background: #ffffff;
          border-radius: 4px;
          font-size: 0.85rem;
          color: #172019;
          outline: none;
        }
        .modal-text-input:focus {
          border-color: #0f5f4f;
          box-shadow: 0 0 0 2px rgba(15, 95, 79, 0.2);
        }
        .profile-hero-card {
          display: grid;
          grid-template-columns: 100px minmax(0, 1fr);
          gap: 28px;
          align-items: start;
          padding: 32px;
          border: 2px solid #172019;
          background: #ffffff;
          box-shadow: 6px 6px 0 #172019;
          border-radius: 8px;
          margin-bottom: 28px;
        }
        .profile-avatar-box {
          position: relative;
          width: 96px;
          height: 96px;
          border: 2px solid #172019;
          background: #0f5f4f;
          color: #ffffff;
          display: grid;
          place-items: center;
          font-size: 2.4rem;
          font-family: Georgia, serif;
          font-weight: 700;
          box-shadow: 4px 4px 0 #172019;
          border-radius: 6px;
          transition: transform 0.15s ease, box-shadow 0.15s ease;
        }
        .profile-avatar-box:hover {
          transform: translate(-1px, -1px);
          box-shadow: 5px 5px 0 #172019;
        }
        .edit-avatar-hint {
          position: absolute;
          bottom: -8px;
          right: -8px;
          padding: 2px 6px;
          background: #ffffff;
          color: #172019;
          border: 1px solid #172019;
          border-radius: 3px;
          font-size: 0.60rem;
          font-weight: 850;
          text-transform: uppercase;
          box-shadow: 1px 1px 0 #172019;
        }
        .hero-kicker-row {
          display: flex;
          align-items: center;
          gap: 10px;
          margin-bottom: 4px;
        }
        .profile-kicker {
          font-size: 0.62rem;
          font-weight: 900;
          letter-spacing: 0.12em;
          color: #0f5f4f;
        }
        .role-badge {
          font-size: 0.58rem;
          font-weight: 900;
          padding: 2px 6px;
          border-radius: 3px;
        }
        .role-badge.resident {
          background: #dce8dd;
          color: #0f5f4f;
        }
        .role-badge.supervisor {
          background: #172019;
          color: #ffffff;
        }
        .role-badge.field {
          background: #e84d7a;
          color: #ffffff;
        }
        .role-badge.guest {
          background: #fef08a;
          color: #854d0e;
        }
        .profile-name-heading {
          font-size: clamp(2.2rem, 3.8vw, 3.2rem);
          font-family: Georgia, serif;
          margin: 4px 0 6px;
          color: #172019;
          line-height: 1.05;
        }
        .profile-role-sub {
          font-size: 0.95rem;
          color: #495248;
          font-weight: 700;
          margin: 0 0 4px;
        }
        .profile-ward-text {
          font-size: 0.85rem;
          color: #687067;
          margin: 0 0 14px;
        }
        .guest-banner-row {
          display: inline-flex;
          align-items: center;
          gap: 12px;
          padding: 8px 14px;
          background: #fbf9f4;
          border: 1px solid #172019;
          border-radius: 6px;
          margin: 4px 0 18px;
          flex-wrap: wrap;
        }
        .profile-header-actions {
          display: flex;
          align-items: center;
          gap: 12px;
          flex-wrap: wrap;
          padding-top: 14px;
          border-top: 1px solid #e2ded4;
        }
        .persona-switcher-kicker {
          font-size: 0.62rem;
          font-weight: 900;
          letter-spacing: 0.1em;
          color: #687067;
        }
        .persona-pill-group {
          display: flex;
          gap: 8px;
          flex-wrap: wrap;
        }
        .persona-pill {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          padding: 6px 12px;
          border: 1px solid #172019;
          background: #fbf9f4;
          border-radius: 4px;
          font-size: 0.74rem;
          font-weight: 800;
          cursor: pointer;
          transition: all 0.15s ease;
        }
        .persona-pill:hover {
          background: #ffffff;
        }
        .persona-pill.active {
          background: #172019;
          color: #ffffff;
          box-shadow: 2px 2px 0 #0f5f4f;
        }
        .signout-pill {
          background: #faf2f2;
          color: #b91c1c;
          border-color: #f87171;
        }
        .profile-stats-ribbon {
          display: grid;
          grid-template-columns: repeat(4, 1fr);
          border: 2px solid #172019;
          background: #ffffff;
          box-shadow: 5px 5px 0 #172019;
          border-radius: 8px;
          margin-bottom: 32px;
          overflow: hidden;
        }
        .stat-tile {
          padding: 20px 22px;
          border-right: 1px solid #e2ded4;
          display: flex;
          flex-direction: column;
          gap: 4px;
        }
        .stat-tile:last-child {
          border-right: 0;
        }
        .stat-label {
          font-size: 0.6rem;
          font-weight: 900;
          letter-spacing: 0.1em;
          color: #0f5f4f;
        }
        .stat-num {
          font-size: 1.6rem;
          font-family: Georgia, serif;
          color: #172019;
          line-height: 1;
        }
        .alert-num {
          color: #b45309;
        }
        .good-num {
          color: #0f5f4f;
        }
        .stat-tile small {
          font-size: 0.72rem;
          color: #687067;
        }
        .profile-tabs-nav {
          display: flex;
          gap: 8px;
          margin-bottom: 24px;
          overflow-x: auto;
        }
        .tab-nav-btn {
          display: inline-flex;
          align-items: center;
          gap: 8px;
          padding: 10px 18px;
          border: 1px solid #172019;
          background: #ffffff;
          border-radius: 6px;
          font-size: 0.8rem;
          font-weight: 800;
          cursor: pointer;
          color: #555e54;
          box-shadow: 2px 2px 0 #172019;
          transition: all 0.15s ease;
          white-space: nowrap;
        }
        .tab-nav-btn:hover {
          background: #fbf9f4;
          color: #172019;
        }
        .tab-nav-btn.active {
          background: #172019;
          color: #ffffff;
          box-shadow: 3px 3px 0 #e84d7a;
        }
        .clarification-callout-card {
          border: 2px solid #b45309;
          background: #fffbeb;
          padding: 20px;
          border-radius: 6px;
          margin-bottom: 32px;
        }
        .callout-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 8px;
        }
        .callout-title-row {
          display: flex;
          align-items: center;
          gap: 8px;
          color: #92400e;
        }
        .callout-body {
          font-size: 0.9rem;
          color: #78350f;
          margin: 0 0 14px;
          line-height: 1.45;
        }
        .clarification-form {
          display: flex;
          gap: 10px;
        }
        .clarification-input {
          flex: 1;
          padding: 10px 14px;
          border: 1px solid #172019;
          background: #ffffff;
          font-size: 0.85rem;
          border-radius: 4px;
          outline: none;
        }
        .clarification-success {
          padding: 10px 14px;
          background: #dce8dd;
          border: 1px solid #0f5f4f;
          color: #0f5f4f;
          font-size: 0.82rem;
          font-weight: 800;
          border-radius: 4px;
        }
        .recent-reports-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 16px;
        }
        .recent-reports-header h3 {
          font-size: 1.3rem;
          font-family: Georgia, serif;
          margin: 0;
          color: #172019;
        }
        .workspace-link {
          font-size: 0.8rem;
          font-weight: 800;
          color: #0f5f4f;
          text-decoration: none;
        }
        .reports-dossier-list {
          display: flex;
          flex-direction: column;
          gap: 12px;
        }
        .report-row-card {
          display: grid;
          grid-template-columns: 140px 1fr auto auto;
          gap: 20px;
          align-items: center;
          padding: 18px 22px;
          border: 1px solid #172019;
          background: #ffffff;
          box-shadow: 3px 3px 0 #172019;
          border-radius: 6px;
        }
        .rpt-id-tag {
          font-size: 0.74rem;
          font-weight: 900;
          color: #e84d7a;
          display: block;
        }
        .linked-inc {
          font-size: 0.65rem;
          color: #687067;
          font-weight: 700;
        }
        .rpt-title {
          font-size: 0.92rem;
          color: #172019;
          display: block;
          margin-bottom: 2px;
        }
        .rpt-loc {
          font-size: 0.76rem;
          color: #0f5f4f;
          font-weight: 750;
          margin: 0 0 2px;
        }
        .rpt-action {
          font-size: 0.72rem;
          color: #687067;
          display: block;
        }
        .rpt-status-col {
          display: flex;
          flex-direction: column;
          align-items: flex-end;
          gap: 4px;
        }
        .rpt-date {
          font-size: 0.68rem;
          color: #687067;
        }
        .timeline-list {
          display: flex;
          flex-direction: column;
          gap: 20px;
          margin-top: 24px;
        }
        .timeline-item {
          display: grid;
          grid-template-columns: 44px 1fr;
          gap: 18px;
        }
        .timeline-marker {
          width: 44px;
          height: 44px;
          border: 2px solid #172019;
          background: #fbf9f4;
          border-radius: 50%;
          display: grid;
          place-items: center;
          font-size: 0.85rem;
          font-weight: 900;
          color: #0f5f4f;
        }
        .timeline-card {
          border: 1px solid #172019;
          background: #ffffff;
          padding: 20px;
          border-radius: 6px;
          box-shadow: 3px 3px 0 #172019;
        }
        .timeline-card-top {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          margin-bottom: 8px;
        }
        .timeline-ref {
          font-size: 0.68rem;
          font-weight: 900;
          color: #e84d7a;
          display: block;
        }
        .timeline-card-top h3 {
          font-size: 1.1rem;
          font-family: Georgia, serif;
          margin: 2px 0 0;
          color: #172019;
        }
        .timeline-meta {
          font-size: 0.78rem;
          color: #0f5f4f;
          font-weight: 750;
          margin: 0 0 6px;
        }
        .timeline-detail {
          font-size: 0.82rem;
          color: #495248;
          margin: 0 0 14px;
        }
        .ward-cards-grid {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 18px;
          margin-top: 24px;
        }
        .ward-select-card {
          border: 1px solid #172019;
          background: #ffffff;
          padding: 20px;
          border-radius: 6px;
          box-shadow: 3px 3px 0 #172019;
        }
        .ward-select-card.active {
          border: 2px solid #0f5f4f;
          background: #f4f8f5;
        }
        .ward-card-header {
          display: flex;
          align-items: center;
          gap: 8px;
          margin-bottom: 8px;
        }
        .ward-select-card p {
          font-size: 0.82rem;
          color: #555e54;
          line-height: 1.5;
          margin: 0 0 14px;
        }
        .geofence-status {
          font-size: 0.72rem;
          font-weight: 850;
          color: #0f5f4f;
        }
        .geofence-status.idle {
          color: #687067;
        }
        .settings-box {
          border: 1px solid #172019;
          background: #ffffff;
          padding: 24px;
          border-radius: 6px;
          box-shadow: 3px 3px 0 #172019;
          margin-top: 24px;
          display: flex;
          flex-direction: column;
          gap: 18px;
        }
        .settings-row {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding-bottom: 14px;
          border-bottom: 1px solid #e2ded4;
        }
        .settings-row:last-child {
          border-bottom: 0;
          padding-bottom: 0;
        }
        .settings-row b {
          font-size: 0.86rem;
          display: block;
          color: #172019;
        }
        .settings-row p {
          font-size: 0.78rem;
          color: #687067;
          margin: 2px 0 0;
          max-width: 580px;
        }
        .verified-pill {
          padding: 4px 10px;
          border: 1px solid #0f5f4f;
          background: #dce8dd;
          color: #0f5f4f;
          font-size: 0.72rem;
          font-weight: 850;
          border-radius: 4px;
        }
        .settings-checkbox {
          width: 18px;
          height: 18px;
          accent-color: #0f5f4f;
        }
        @media (max-width: 860px) {
          .profile-hero-card {
            grid-template-columns: 1fr;
          }
          .profile-stats-ribbon {
            grid-template-columns: 1fr 1fr;
          }
          .report-row-card {
            grid-template-columns: 1fr;
          }
          .rpt-status-col {
            align-items: flex-start;
          }
          .ward-cards-grid {
            grid-template-columns: 1fr;
          }
        }
        @media (max-width: 540px) {
          .profile-stats-ribbon {
            grid-template-columns: 1fr;
          }
          .clarification-form {
            flex-direction: column;
          }
        }
      `}</style>
    </>
  );
}
