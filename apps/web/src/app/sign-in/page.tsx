"use client";

import { FormEvent, useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Footer, Nav } from "@/components/site";
import { FlatIcon } from "@/components/flat-icons";
import { signInWithPassword, signUpWithPassword } from "@/lib/auth";

interface LiveMetricNode {
  id: string;
  tag: string;
  title: string;
  description: string;
  time: string;
  statusColor: string;
}

const TELEMETRY_FEED: LiveMetricNode[] = [
  {
    id: "N1",
    tag: "POSTGIS 3.4 GEOPROCESSOR",
    title: "School Safety Buffer Triggered (14m)",
    description: "Geotag within DAV Public School corridor deterministically raised priority to P1 Critical.",
    time: "Illustrative Trace",
    statusColor: "#0f5f4f",
  },
  {
    id: "N2",
    tag: "ZERO-SHOT CLIP VISION",
    title: "Defect Verification: High Confidence",
    description: "Asphalt pooling and surface fissure confirmed without hallucinated claims.",
    time: "Illustrative Trace",
    statusColor: "#e84d7a",
  },
  {
    id: "N3",
    tag: "LANGGRAPH AGENT GRAPH",
    title: "Policy Grounded: PLAY-WATER-01",
    description: "Retrieved municipal playbook for Ward 12 distribution repair.",
    time: "Illustrative Trace",
    statusColor: "#0f5f4f",
  },
  {
    id: "N4",
    tag: "SUPERVISOR GATEWAY",
    title: "Work Order Authorized: WO-2026-0881",
    description: "Certified municipal supervisor signed off on ductile sleeve dispatch.",
    time: "Illustrative Trace",
    statusColor: "#172019",
  },
];

export default function SignIn() {
  const router = useRouter();
  const [isSignUp, setIsSignUp] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [notice, setNotice] = useState("");
  const [authError, setAuthError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [activeFeedIndex, setActiveFeedIndex] = useState(0);

  // Auto-cycle live telemetry items
  useEffect(() => {
    const timer = setInterval(() => {
      setActiveFeedIndex((prev) => (prev + 1) % TELEMETRY_FEED.length);
    }, 4000);
    return () => clearInterval(timer);
  }, []);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setAuthError(null);
    setNotice("");

    try {
      if (isSignUp) {
        const result = await signUpWithPassword(email, password, name);
        if (result.confirmationRequired) {
          setNotice("Account created. Check your email to confirm your address, then sign in to Civitas.");
          setIsSignUp(false);
        } else if (result.user) {
          setNotice(`Welcome to Civitas, ${result.user.name}. Your account is active.`);
          setTimeout(() => {
            router.push(result.user?.role === "reviewer" || result.user?.role === "supervisor" ? "/workspace" : "/profile");
          }, 600);
        }
      } else {
        const user = await signInWithPassword(email, password);
        setNotice(`Welcome back, ${user.name}. Signed in successfully.`);
        setTimeout(() => {
          router.push(user.role === "reviewer" || user.role === "supervisor" ? "/workspace" : "/profile");
        }, 600);
      }
    } catch (err) {
      setAuthError(err instanceof Error ? err.message : "Authentication failed. Please check your credentials.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const activeNode = TELEMETRY_FEED[activeFeedIndex];

  return (
    <>
      <Nav />
      <main className="auth-page-shell">
        <div className="auth-layout-grid">
          {/* LEFT: CIVIC INTELLIGENCE & TELEMETRY SHOWCASE */}
          <section className="auth-hero-column" aria-label="Platform overview">
            <div className="auth-hero-badge">
              <span className="live-pulsing-badge" />
              <span>CIVITAS ACCESS & GOVERNANCE</span>
            </div>

            <h1 className="auth-hero-title">
              Evidence-Backed Civic Incident <span className="title-accent">Intelligence</span>
            </h1>

            <p className="auth-hero-lead">
              Access your personal report tracking dossier, view real-time field repair checkpoints, or authorize municipal work orders with verified audit trails.
            </p>

            {/* LIVE TELEMETRY STREAM CARD */}
            <div className="telemetry-card">
              <div className="telemetry-top-bar">
                <div className="telemetry-tag-group">
                  <FlatIcon name="workflow" size={14} color="#0f5f4f" />
                  <span className="telemetry-tag">{activeNode.tag}</span>
                </div>
                <span className="telemetry-time">{activeNode.time}</span>
              </div>

              <b className="telemetry-node-title">{activeNode.title}</b>
              <p className="telemetry-node-desc">{activeNode.description}</p>

              <div className="telemetry-stepper-row">
                {TELEMETRY_FEED.map((item, idx) => (
                  <button
                    key={item.id}
                    type="button"
                    className={`stepper-pill-btn ${idx === activeFeedIndex ? "active" : ""}`}
                    onClick={() => setActiveFeedIndex(idx)}
                    aria-label={`View telemetry node ${idx + 1}`}
                  >
                    <span className="stepper-bar-fill" />
                  </button>
                ))}
              </div>
            </div>

            {/* PLATFORM GUARANTEES */}
            <div className="guarantees-grid">
              <div className="guarantee-tile">
                <div className="guarantee-icon-wrap obs">
                  <FlatIcon name="camera" size={16} color="#0f5f4f" />
                </div>
                <div>
                  <b>Observable Evidence</b>
                  <p>Model outputs never overwrite citizen claims</p>
                </div>
              </div>

              <div className="guarantee-tile">
                <div className="guarantee-icon-wrap rep">
                  <FlatIcon name="map" size={16} color="#172019" />
                </div>
                <div>
                  <b>PostGIS 3.4 Clustering</b>
                  <p>500m School and Hospital safety buffers</p>
                </div>
              </div>

              <div className="guarantee-tile">
                <div className="guarantee-icon-wrap inf">
                  <FlatIcon name="shield" size={16} color="#e84d7a" />
                </div>
                <div>
                  <b>Supervisor Gate</b>
                  <p>1-click human review for work-order dispatch</p>
                </div>
              </div>
            </div>
          </section>

          {/* RIGHT: AUTHENTICATION CARD */}
          <section className="auth-form-column">
            <div className="auth-form-container">
              {/* SEGMENTED TAB TOGGLE */}
              <div className="segmented-tab-row" role="tablist">
                <button
                  type="button"
                  role="tab"
                  aria-selected={!isSignUp}
                  className={`tab-segment-btn ${!isSignUp ? "active" : ""}`}
                  onClick={() => {
                    setIsSignUp(false);
                    setNotice("");
                  }}
                >
                  Sign In
                </button>
                <button
                  type="button"
                  role="tab"
                  aria-selected={isSignUp}
                  className={`tab-segment-btn ${isSignUp ? "active" : ""}`}
                  onClick={() => {
                    setIsSignUp(true);
                    setNotice("");
                  }}
                >
                  Create Account
                </button>
              </div>

              <form onSubmit={handleSubmit} className="auth-interactive-form">
                {isSignUp && (
                  <div className="auth-input-group">
                    <label className="input-title-label" htmlFor="user-name-input">
                      Display Name
                    </label>
                    <input
                      id="user-name-input"
                      type="text"
                      required
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      placeholder="e.g. Alex Morgan"
                      className="auth-input-control"
                    />
                  </div>
                )}

                <div className="auth-input-group">
                  <label className="input-title-label" htmlFor="user-email-input">
                    Email Address
                  </label>
                  <input
                    id="user-email-input"
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="name@example.com"
                    className="auth-input-control"
                  />
                </div>

                <div className="auth-input-group">
                  <div className="label-with-pw-toggle">
                    <label className="input-title-label" htmlFor="user-password-input">
                      Password
                    </label>
                    <button
                      type="button"
                      className="eye-pw-btn"
                      onClick={() => setShowPassword(!showPassword)}
                    >
                      <FlatIcon name={showPassword ? "eye-off" : "eye"} size={13} color="#687067" />
                      <span>{showPassword ? "Hide" : "Show"}</span>
                    </button>
                  </div>
                  <input
                    id="user-password-input"
                    type={showPassword ? "text" : "password"}
                    required
                    minLength={8}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="At least 8 characters"
                    className="auth-input-control"
                  />
                </div>

                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="button large submit-action-btn"
                >
                  {isSubmitting
                    ? "Authenticating..."
                    : isSignUp
                    ? "Create Civitas Account →"
                    : "Sign In to Workspace →"}
                </button>

                {isSignUp ? (
                  <p className="signup-tos-notice">
                    By creating an account, you agree to the Civitas{" "}
                    <Link href="/terms">Terms of Service</Link> and{" "}
                    <Link href="/privacy">Privacy Policy</Link>.
                  </p>
                ) : (
                  <div className="reset-pw-row">
                    <span className="reset-pw-hint">Forgot your password?</span>
                    <Link href="/reset-password" className="reset-btn-pill">
                      Reset Password
                    </Link>
                  </div>
                )}

                {authError && (
                  <div className="auth-notice-toast error" role="alert" style={{ background: "rgba(239, 68, 68, 0.12)", border: "1px solid #f87171", color: "#b91c1c", marginTop: "12px" }}>
                    <span>{authError}</span>
                  </div>
                )}

                {notice && (
                  <div className="auth-notice-toast" role="status">
                    <FlatIcon name="check" size={14} color="#0f5f4f" />
                    <span>{notice}</span>
                  </div>
                )}

                <div className="demo-personas-section" style={{ marginTop: "24px", paddingTop: "20px", borderTop: "1px dashed #d9d7ce" }}>
                  <span style={{ fontSize: "0.68rem", fontWeight: 800, color: "#687067", letterSpacing: "0.08em" }}>
                    DEMO PERSONAS (PRE-CONFIGURED ROLES)
                  </span>
                  <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "8px", marginTop: "10px" }}>
                    <button
                      type="button"
                      onClick={() => {
                        setEmail("supervisor.chen@bhubaneswar.gov.in");
                        setPassword("SupervisorPass123!");
                        setName("Sarah Chen");
                        setIsSignUp(false);
                      }}
                      className="demo-persona-chip"
                      style={{
                        padding: "8px 10px",
                        fontSize: "0.75rem",
                        textAlign: "left",
                        border: "1px solid #172019",
                        background: email.includes("supervisor") ? "#e6f4ea" : "#fdfcf9",
                        borderRadius: "4px",
                        cursor: "pointer",
                        fontWeight: 600,
                      }}
                    >
                      <b>Supervisor</b>
                      <span style={{ display: "block", fontSize: "0.65rem", color: "#687067" }}>Review gate</span>
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        setEmail("field.dispatch@waterdept.gov.in");
                        setPassword("FieldDispatch123!");
                        setName("Marcus Vance");
                        setIsSignUp(false);
                      }}
                      className="demo-persona-chip"
                      style={{
                        padding: "8px 10px",
                        fontSize: "0.75rem",
                        textAlign: "left",
                        border: "1px solid #172019",
                        background: email.includes("field") ? "#e6f4ea" : "#fdfcf9",
                        borderRadius: "4px",
                        cursor: "pointer",
                        fontWeight: 600,
                      }}
                    >
                      <b>Field Lead</b>
                      <span style={{ display: "block", fontSize: "0.65rem", color: "#687067" }}>Crew dispatch</span>
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        setEmail("ananya.resident@civic.local");
                        setPassword("CitizenPass123!");
                        setName("Ananya Sharma");
                        setIsSignUp(false);
                      }}
                      className="demo-persona-chip"
                      style={{
                        padding: "8px 10px",
                        fontSize: "0.75rem",
                        textAlign: "left",
                        border: "1px solid #172019",
                        background: email.includes("ananya") ? "#e6f4ea" : "#fdfcf9",
                        borderRadius: "4px",
                        cursor: "pointer",
                        fontWeight: 600,
                      }}
                    >
                      <b>Citizen</b>
                      <span style={{ display: "block", fontSize: "0.65rem", color: "#687067" }}>Resident</span>
                    </button>
                  </div>
                </div>
              </form>

              <div className="auth-terms-footer">
                <small>
                  Protected by cryptographic evidence trails · <Link href="/privacy">Privacy</Link> ·{" "}
                  <Link href="/terms">Terms of Service</Link>
                </small>
              </div>
            </div>
          </section>
        </div>
      </main>

      {/* STANDARD SITE FOOTER */}
      <Footer />

      <style jsx>{`
        .auth-page-shell {
          width: min(calc(100% - 40px), 1180px);
          margin: 48px auto 90px;
        }
        .auth-layout-grid {
          display: grid;
          grid-template-columns: 1.15fr 0.85fr;
          gap: 54px;
          align-items: start;
        }
        .auth-hero-column {
          display: flex;
          flex-direction: column;
          gap: 20px;
        }
        .auth-hero-badge {
          display: inline-flex;
          align-items: center;
          gap: 8px;
          padding: 4px 10px;
          border: 1px solid #0f5f4f;
          background: #dce8dd;
          color: #0f5f4f;
          border-radius: 4px;
          font-size: 0.65rem;
          font-weight: 900;
          letter-spacing: 0.1em;
          width: fit-content;
        }
        .live-pulsing-badge {
          width: 7px;
          height: 7px;
          border-radius: 50%;
          background: #0f5f4f;
          animation: pulseGlow 1.8s infinite ease-in-out;
        }
        @keyframes pulseGlow {
          0% {
            transform: scale(0.9);
            box-shadow: 0 0 0 0 rgba(15, 95, 79, 0.7);
          }
          70% {
            transform: scale(1.15);
            box-shadow: 0 0 0 6px rgba(15, 95, 79, 0);
          }
          100% {
            transform: scale(0.9);
            box-shadow: 0 0 0 0 rgba(15, 95, 79, 0);
          }
        }
        .auth-hero-title {
          font-size: clamp(2.3rem, 4vw, 3.4rem);
          font-family: Georgia, serif;
          margin: 0;
          color: #172019;
          line-height: 1.08;
        }
        .title-accent {
          color: #0f5f4f;
          font-style: italic;
        }
        .auth-hero-lead {
          font-size: 1rem;
          color: #555e54;
          line-height: 1.6;
          margin: 0;
          max-width: 580px;
        }
        .telemetry-card {
          border: 2px solid #172019;
          background: #ffffff;
          box-shadow: 6px 6px 0 #172019;
          border-radius: 8px;
          padding: 20px 24px;
          display: flex;
          flex-direction: column;
          gap: 10px;
          transition: transform 0.2s ease;
        }
        .telemetry-top-bar {
          display: flex;
          justify-content: space-between;
          align-items: center;
        }
        .telemetry-tag-group {
          display: flex;
          align-items: center;
          gap: 7px;
        }
        .telemetry-tag {
          font-size: 0.62rem;
          font-weight: 900;
          letter-spacing: 0.1em;
          color: #0f5f4f;
        }
        .telemetry-time {
          font-size: 0.68rem;
          font-weight: 700;
          color: #687067;
        }
        .telemetry-node-title {
          font-size: 0.95rem;
          color: #172019;
          line-height: 1.3;
        }
        .telemetry-node-desc {
          font-size: 0.82rem;
          color: #555e54;
          line-height: 1.45;
          margin: 0;
        }
        .telemetry-stepper-row {
          display: flex;
          gap: 6px;
          padding-top: 6px;
        }
        .stepper-pill-btn {
          flex: 1;
          height: 6px;
          background: #e2ded4;
          border: 0;
          border-radius: 3px;
          padding: 0;
          cursor: pointer;
          transition: background 0.2s ease;
        }
        .stepper-pill-btn.active {
          background: #0f5f4f;
        }
        .guarantees-grid {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 12px;
        }
        .guarantee-tile {
          display: flex;
          align-items: flex-start;
          gap: 10px;
          padding: 12px;
          border: 1px solid #e2ded4;
          background: #ffffff;
          border-radius: 6px;
        }
        .guarantee-icon-wrap {
          width: 30px;
          height: 30px;
          border-radius: 4px;
          display: grid;
          place-items: center;
          flex-shrink: 0;
          border: 1px solid #172019;
        }
        .guarantee-icon-wrap.obs {
          background: #dce8dd;
        }
        .guarantee-icon-wrap.rep {
          background: #fbf9f4;
        }
        .guarantee-icon-wrap.inf {
          background: #fce7f3;
        }
        .guarantee-tile b {
          display: block;
          font-size: 0.76rem;
          color: #172019;
          line-height: 1.2;
          margin-bottom: 2px;
        }
        .guarantee-tile p {
          font-size: 0.68rem;
          color: #687067;
          line-height: 1.3;
          margin: 0;
        }
        .auth-form-column {
          display: flex;
          justify-content: center;
        }
        .auth-form-container {
          width: 100%;
          max-width: 440px;
          border: 2px solid #172019;
          background: #ffffff;
          box-shadow: 7px 7px 0 #172019;
          border-radius: 8px;
          padding: 28px 32px;
          display: flex;
          flex-direction: column;
          gap: 20px;
        }
        .segmented-tab-row {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 4px;
          background: #fbf9f4;
          border: 1px solid #172019;
          padding: 4px;
          border-radius: 6px;
        }
        .tab-segment-btn {
          border: 0;
          background: transparent;
          padding: 9px 14px;
          font-size: 0.85rem;
          font-weight: 800;
          border-radius: 4px;
          cursor: pointer;
          color: #555e54;
          transition: all 0.15s ease;
        }
        .tab-segment-btn.active {
          background: #172019;
          color: #ffffff;
          box-shadow: 2px 2px 0 rgba(0, 0, 0, 0.2);
        }
        .auth-interactive-form {
          display: flex;
          flex-direction: column;
          gap: 16px;
        }
        .auth-input-group {
          display: flex;
          flex-direction: column;
          gap: 5px;
        }
        .input-title-label {
          font-size: 0.8rem;
          font-weight: 800;
          color: #172019;
        }
        .label-with-pw-toggle {
          display: flex;
          justify-content: space-between;
          align-items: center;
        }
        .eye-pw-btn {
          display: inline-flex;
          align-items: center;
          gap: 4px;
          border: 0;
          background: transparent;
          cursor: pointer;
          font-size: 0.72rem;
          font-weight: 750;
          color: #687067;
          padding: 0;
        }
        .eye-pw-btn:hover {
          color: #172019;
        }
        .auth-input-control {
          width: 100%;
          border: 1px solid #172019;
          background: #fbf9f4;
          padding: 11px 14px;
          font-size: 0.9rem;
          border-radius: 4px;
          outline: none;
          font-family: inherit;
          transition: border-color 0.15s ease, background 0.15s ease;
        }
        .auth-input-control:focus {
          background: #ffffff;
          border-color: #0f5f4f;
          box-shadow: 0 0 0 2px rgba(15, 95, 79, 0.15);
        }
        .submit-action-btn {
          width: 100%;
          margin-top: 4px;
          padding: 12px 18px;
        }
        .reset-pw-row {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 8px;
          margin-top: -2px;
        }
        .reset-pw-hint {
          font-size: 0.72rem;
          color: #687067;
        }
        .reset-btn-pill {
          display: inline-flex;
          align-items: center;
          padding: 3px 10px;
          font-size: 0.7rem;
          font-weight: 750;
          color: #172019;
          background: #fbf9f4;
          border: 1px solid #172019;
          border-radius: 4px;
          text-decoration: none;
          box-shadow: 1px 1px 0 #172019;
          transition: all 0.15s ease;
          line-height: 1.2;
        }
        .reset-btn-pill:hover {
          background: #172019;
          color: #ffffff;
        }
        .signup-tos-notice {
          font-size: 0.72rem;
          color: #687067;
          line-height: 1.4;
          text-align: center;
          margin: -2px 0 0;
        }
        .signup-tos-notice a {
          color: #0f5f4f;
          font-weight: 700;
          text-decoration: underline;
        }
        .auth-notice-toast {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 10px 14px;
          background: #f4f8f5;
          border: 1px solid #0f5f4f;
          color: #0f5f4f;
          font-size: 0.8rem;
          font-weight: 750;
          border-radius: 4px;
          line-height: 1.4;
        }
        .auth-terms-footer {
          text-align: center;
          padding-top: 12px;
          border-top: 1px solid #e2ded4;
        }
        .auth-terms-footer small {
          font-size: 0.7rem;
          color: #687067;
        }
        .auth-terms-footer a {
          color: #172019;
          font-weight: 700;
          text-decoration: underline;
        }
        @media (max-width: 960px) {
          .auth-layout-grid {
            grid-template-columns: 1fr;
            gap: 36px;
          }
          .guarantees-grid {
            grid-template-columns: 1fr;
          }
        }
      `}</style>
    </>
  );
}
