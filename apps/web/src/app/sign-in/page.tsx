"use client";

import { FormEvent, useState, useEffect } from "react";
import Link from "next/link";
import { Nav } from "@/components/site";
import { OnboardingPanel } from "@/components/onboarding-panel";
import { FlatIcon } from "@/components/flat-icons";

interface LiveEvent {
  id: string;
  time: string;
  type: "intake" | "spatial" | "vision" | "gate";
  tag: string;
  title: string;
  detail: string;
}

const LIVE_STREAM_EVENTS: LiveEvent[] = [
  {
    id: "EV-01",
    time: "Just now",
    type: "spatial",
    tag: "POSTGIS 3.4",
    title: "School Buffer Trigger (14m)",
    detail: "Geotag within DAV Public School corridor escalated to P1 priority.",
  },
  {
    id: "EV-02",
    time: "12s ago",
    type: "vision",
    tag: "ZERO-SHOT CLIP",
    title: "Defect Verification: 98.4%",
    detail: "Asphalt cavity and liquid pooling confirmed against citizen claim.",
  },
  {
    id: "EV-03",
    time: "35s ago",
    type: "intake",
    tag: "LANGGRAPH AGENT",
    title: "Policy Grounded: PLAY-WATER-01",
    detail: "Retrieved municipal playbook for Ward 12 distribution repair.",
  },
  {
    id: "EV-04",
    time: "1m ago",
    type: "gate",
    tag: "SUPERVISOR GATE",
    title: "Work Order Authorized",
    detail: "Supervisor signed off on ductile collar dispatch for WO-2026-0881.",
  },
];

export default function SignIn() {
  const [create, setCreate] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [notice, setNotice] = useState("");
  const [onboarding, setOnboarding] = useState(false);
  const [activeStreamIndex, setActiveStreamIndex] = useState(0);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Auto-cycle live telemetry stream
  useEffect(() => {
    const timer = setInterval(() => {
      setActiveStreamIndex((prev) => (prev + 1) % LIVE_STREAM_EVENTS.length);
    }, 3800);
    return () => clearInterval(timer);
  }, []);

  const submit = (event: FormEvent) => {
    event.preventDefault();
    setIsSubmitting(true);

    setTimeout(() => {
      setIsSubmitting(false);
      if (create) {
        setOnboarding(true);
      } else {
        const userName = name || (email ? email.split("@")[0] : "Resident");
        const userData = {
          name: userName,
          email: email || "dhruvg.030304@gmail.com",
          role: "resident" as const,
          roleTitle: "Registered Citizen · Ward 12",
          ward: "Ward 12 · DAV Public School Zone",
          avatarInitials: userName.slice(0, 2).toUpperCase(),
        };
        try {
          localStorage.setItem("civitas_current_user", JSON.stringify(userData));
        } catch {
          // ignore
        }
        setNotice(`Welcome back, ${userName}! Signed in successfully to your Civitas workspace.`);
      }
    }, 600);
  };

  const currentEvent = LIVE_STREAM_EVENTS[activeStreamIndex];

  return (
    <div className="auth-viewport-root">
      <Nav />

      <main className="auth-viewport-main">
        <div className="auth-split-container">
          {/* LEFT COLUMN: DYNAMIC ANIMATED CIVIC INTELLIGENCE SHOWCASE */}
          <section className="civic-intel-panel" aria-label="Civitas Intelligence Telemetry">
            <div className="intel-header">
              <div className="live-status-pill">
                <span className="live-pulsing-dot" />
                <span>SECURE CIVIC RUNTIME · WARD 12</span>
              </div>
              <h1 className="intel-headline">
                Civic Incident <span className="highlight-text">Intelligence</span> & Governance
              </h1>
              <p className="intel-sub">
                Evidence-backed civic coordination where observed facts, policy retrieval, model inferences, and human decisions stay strictly distinct.
              </p>
            </div>

            {/* ANIMATED LIVE TELEMETRY STREAM CARD */}
            <div className="telemetry-stream-card">
              <div className="stream-card-top">
                <div className="stream-kicker-group">
                  <FlatIcon name="workflow" size={14} color="#0f5f4f" />
                  <span className="stream-kicker">LIVE PIPELINE STREAM</span>
                </div>
                <span className="stream-time-badge">{currentEvent.time}</span>
              </div>

              <div className="stream-content-body">
                <div className="stream-event-row">
                  <span className={`event-type-tag ${currentEvent.type}`}>
                    {currentEvent.tag}
                  </span>
                  <b className="event-title">{currentEvent.title}</b>
                </div>
                <p className="event-detail">{currentEvent.detail}</p>
              </div>

              {/* STREAM STEPPER INDICATORS */}
              <div className="stream-indicators-row">
                {LIVE_STREAM_EVENTS.map((ev, idx) => (
                  <button
                    key={ev.id}
                    type="button"
                    className={`stream-dot-btn ${idx === activeStreamIndex ? "active" : ""}`}
                    onClick={() => setActiveStreamIndex(idx)}
                    aria-label={`View telemetry step ${idx + 1}`}
                  >
                    <span className="dot-bar" />
                  </button>
                ))}
              </div>
            </div>

            {/* THREE CORE GOVERNANCE PILLARS */}
            <div className="governance-triad-grid">
              <div className="triad-item">
                <div className="triad-icon-wrap obs">
                  <FlatIcon name="camera" size={15} color="#0f5f4f" />
                </div>
                <div>
                  <b>Observable Media</b>
                  <small>Zero-shot defect classification</small>
                </div>
              </div>

              <div className="triad-item">
                <div className="triad-icon-wrap rep">
                  <FlatIcon name="map" size={15} color="#172019" />
                </div>
                <div>
                  <b>PostGIS Clustering</b>
                  <small>500m School/Hospital buffers</small>
                </div>
              </div>

              <div className="triad-item">
                <div className="triad-icon-wrap inf">
                  <FlatIcon name="shield" size={15} color="#e84d7a" />
                </div>
                <div>
                  <b>Human Authorization</b>
                  <small>1-click supervisor sign-off</small>
                </div>
              </div>
            </div>
          </section>

          {/* RIGHT COLUMN: AUTHENTICATION FORM CARD */}
          <section className="auth-form-panel">
            <div className="auth-form-card">
              {/* TAB SWITCHER */}
              <div className="auth-tab-bar" role="tablist">
                <button
                  type="button"
                  role="tab"
                  aria-selected={!create}
                  className={`tab-toggle ${!create ? "active" : ""}`}
                  onClick={() => {
                    setCreate(false);
                    setNotice("");
                  }}
                >
                  Sign In
                </button>
                <button
                  type="button"
                  role="tab"
                  aria-selected={create}
                  className={`tab-toggle ${create ? "active" : ""}`}
                  onClick={() => {
                    setCreate(true);
                    setNotice("");
                  }}
                >
                  Create Account
                </button>
              </div>

              <form onSubmit={submit} className="auth-inputs-form">
                {create && (
                  <div className="form-input-group">
                    <label className="input-label" htmlFor="auth-name">
                      Full Name
                    </label>
                    <input
                      id="auth-name"
                      type="text"
                      required
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      placeholder="e.g. Dhruv Gupta"
                      className="auth-text-field"
                    />
                  </div>
                )}

                <div className="form-input-group">
                  <label className="input-label" htmlFor="auth-email">
                    Email Address
                  </label>
                  <input
                    id="auth-email"
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="dhruvg.030304@gmail.com"
                    className="auth-text-field"
                  />
                </div>

                <div className="form-input-group">
                  <div className="label-with-action">
                    <label className="input-label" htmlFor="auth-password">
                      Password
                    </label>
                    <button
                      type="button"
                      className="pw-toggle-btn"
                      onClick={() => setShowPassword(!showPassword)}
                    >
                      <FlatIcon name={showPassword ? "eye-off" : "eye"} size={13} color="#687067" />
                      <span>{showPassword ? "Hide" : "Show"}</span>
                    </button>
                  </div>
                  <input
                    id="auth-password"
                    type={showPassword ? "text" : "password"}
                    required
                    minLength={8}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Enter password (min 8 chars)"
                    className="auth-text-field"
                  />
                </div>

                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="button large auth-action-btn"
                >
                  {isSubmitting
                    ? "Authenticating..."
                    : create
                    ? "Create Civitas Account →"
                    : "Sign In to Workspace →"}
                </button>

                {!create && (
                  <div className="forgot-pw-row">
                    <Link href="/reset-password" className="forgot-pw-link">
                      Forgot your password? Reset here →
                    </Link>
                  </div>
                )}

                {notice && (
                  <div className="auth-alert-box" role="status">
                    <FlatIcon name="check" size={14} color="#0f5f4f" />
                    <span>{notice}</span>
                  </div>
                )}
              </form>

              <div className="auth-card-footer">
                <small>
                  Protected by cryptographic evidence trails · <Link href="/privacy">Privacy</Link> ·{" "}
                  <Link href="/terms">Terms</Link>
                </small>
              </div>
            </div>
          </section>
        </div>
      </main>

      {/* COMPACT VIEWPORT FOOTER BAR */}
      <footer className="auth-compact-footer">
        <span>CIVITAS PLATFORM · EVIDENCE-BACKED CIVIC INCIDENT INTELLIGENCE</span>
        <span>POSTGIS 3.4 · LANGGRAPH MULTI-AGENT STATE GRAPH</span>
      </footer>

      {onboarding && (
        <OnboardingPanel
          onClose={() => {
            setOnboarding(false);
            setNotice("✓ Account created. Preferences saved to local session.");
          }}
        />
      )}

      <style jsx>{`
        .auth-viewport-root {
          height: 100vh;
          max-height: 100vh;
          display: flex;
          flex-direction: column;
          background: #fbf9f4;
          overflow: hidden;
        }
        .auth-viewport-main {
          flex: 1;
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 12px 24px;
          min-height: 0;
        }
        .auth-split-container {
          width: min(100%, 1160px);
          display: grid;
          grid-template-columns: 1.15fr 0.85fr;
          gap: 40px;
          align-items: center;
        }
        .civic-intel-panel {
          display: flex;
          flex-direction: column;
          gap: 16px;
        }
        .intel-header {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }
        .live-status-pill {
          display: inline-flex;
          align-items: center;
          gap: 7px;
          padding: 3px 9px;
          border: 1px solid #0f5f4f;
          background: #dce8dd;
          color: #0f5f4f;
          border-radius: 4px;
          font-size: 0.62rem;
          font-weight: 900;
          letter-spacing: 0.1em;
          width: fit-content;
        }
        .live-pulsing-dot {
          width: 7px;
          height: 7px;
          border-radius: 50%;
          background: #0f5f4f;
          animation: pulse 1.8s infinite ease-in-out;
        }
        @keyframes pulse {
          0% {
            transform: scale(0.9);
            box-shadow: 0 0 0 0 rgba(15, 95, 79, 0.7);
          }
          70% {
            transform: scale(1.1);
            box-shadow: 0 0 0 6px rgba(15, 95, 79, 0);
          }
          100% {
            transform: scale(0.9);
            box-shadow: 0 0 0 0 rgba(15, 95, 79, 0);
          }
        }
        .intel-headline {
          font-size: clamp(2rem, 3.4vw, 2.9rem);
          font-family: Georgia, serif;
          margin: 0;
          color: #172019;
          line-height: 1.08;
        }
        .highlight-text {
          color: #0f5f4f;
          font-style: italic;
        }
        .intel-sub {
          font-size: 0.88rem;
          color: #555e54;
          line-height: 1.5;
          margin: 0;
          max-width: 520px;
        }
        .telemetry-stream-card {
          border: 2px solid #172019;
          background: #ffffff;
          box-shadow: 5px 5px 0 #172019;
          border-radius: 8px;
          padding: 16px 20px;
          display: flex;
          flex-direction: column;
          gap: 10px;
          transition: transform 0.2s ease;
        }
        .stream-card-top {
          display: flex;
          justify-content: space-between;
          align-items: center;
        }
        .stream-kicker-group {
          display: flex;
          align-items: center;
          gap: 6px;
        }
        .stream-kicker {
          font-size: 0.6rem;
          font-weight: 900;
          letter-spacing: 0.12em;
          color: #0f5f4f;
        }
        .stream-time-badge {
          font-size: 0.65rem;
          color: #687067;
          font-weight: 700;
        }
        .stream-content-body {
          display: flex;
          flex-direction: column;
          gap: 4px;
        }
        .stream-event-row {
          display: flex;
          align-items: center;
          gap: 8px;
        }
        .event-type-tag {
          font-size: 0.58rem;
          font-weight: 900;
          padding: 2px 6px;
          border-radius: 3px;
          border: 1px solid #172019;
        }
        .event-type-tag.spatial {
          background: #e0e7ff;
          color: #3730a3;
        }
        .event-type-tag.vision {
          background: #fce7f3;
          color: #be185d;
        }
        .event-type-tag.intake {
          background: #dce8dd;
          color: #0f5f4f;
        }
        .event-type-tag.gate {
          background: #fee2e2;
          color: #991b1b;
        }
        .event-title {
          font-size: 0.88rem;
          color: #172019;
        }
        .event-detail {
          font-size: 0.78rem;
          color: #555e54;
          margin: 0;
          line-height: 1.4;
        }
        .stream-indicators-row {
          display: flex;
          gap: 6px;
          padding-top: 4px;
        }
        .stream-dot-btn {
          flex: 1;
          height: 5px;
          background: #e2ded4;
          border: 0;
          border-radius: 2px;
          padding: 0;
          cursor: pointer;
          transition: background 0.25s ease;
        }
        .stream-dot-btn.active {
          background: #0f5f4f;
        }
        .governance-triad-grid {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 10px;
        }
        .triad-item {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 10px;
          border: 1px solid #e2ded4;
          background: #ffffff;
          border-radius: 6px;
        }
        .triad-icon-wrap {
          width: 28px;
          height: 28px;
          border-radius: 4px;
          display: grid;
          place-items: center;
          flex-shrink: 0;
          border: 1px solid #172019;
        }
        .triad-icon-wrap.obs {
          background: #dce8dd;
        }
        .triad-icon-wrap.rep {
          background: #fbf9f4;
        }
        .triad-icon-wrap.inf {
          background: #fce7f3;
        }
        .triad-item b {
          display: block;
          font-size: 0.72rem;
          color: #172019;
          line-height: 1.2;
        }
        .triad-item small {
          display: block;
          font-size: 0.62rem;
          color: #687067;
          line-height: 1.2;
        }
        .auth-form-panel {
          display: flex;
          justify-content: center;
        }
        .auth-form-card {
          width: 100%;
          max-width: 440px;
          border: 2px solid #172019;
          background: #ffffff;
          box-shadow: 6px 6px 0 #172019;
          border-radius: 8px;
          padding: 24px 28px;
          display: flex;
          flex-direction: column;
          gap: 16px;
        }
        .auth-tab-bar {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 4px;
          background: #fbf9f4;
          border: 1px solid #172019;
          padding: 3px;
          border-radius: 6px;
        }
        .tab-toggle {
          border: 0;
          background: transparent;
          padding: 8px 12px;
          font-size: 0.82rem;
          font-weight: 800;
          border-radius: 4px;
          cursor: pointer;
          color: #555e54;
          transition: all 0.15s ease;
        }
        .tab-toggle.active {
          background: #172019;
          color: #ffffff;
          box-shadow: 2px 2px 0 rgba(0, 0, 0, 0.2);
        }
        .auth-inputs-form {
          display: flex;
          flex-direction: column;
          gap: 12px;
        }
        .form-input-group {
          display: flex;
          flex-direction: column;
          gap: 4px;
        }
        .input-label {
          font-size: 0.76rem;
          font-weight: 800;
          color: #172019;
        }
        .label-with-action {
          display: flex;
          justify-content: space-between;
          align-items: center;
        }
        .pw-toggle-btn {
          display: inline-flex;
          align-items: center;
          gap: 4px;
          border: 0;
          background: transparent;
          cursor: pointer;
          font-size: 0.7rem;
          font-weight: 750;
          color: #687067;
          padding: 0;
        }
        .pw-toggle-btn:hover {
          color: #172019;
        }
        .auth-text-field {
          width: 100%;
          border: 1px solid #172019;
          background: #fbf9f4;
          padding: 9px 12px;
          font-size: 0.86rem;
          border-radius: 4px;
          outline: none;
          font-family: inherit;
          transition: border-color 0.15s ease, background 0.15s ease;
        }
        .auth-text-field:focus {
          background: #ffffff;
          border-color: #0f5f4f;
          box-shadow: 0 0 0 2px rgba(15, 95, 79, 0.15);
        }
        .auth-action-btn {
          width: 100%;
          margin-top: 4px;
          padding: 11px 16px;
        }
        .forgot-pw-row {
          text-align: center;
          margin-top: -2px;
        }
        .forgot-pw-link {
          font-size: 0.75rem;
          font-weight: 750;
          color: #0f5f4f;
          text-decoration: none;
        }
        .forgot-pw-link:hover {
          color: #e84d7a;
          text-decoration: underline;
        }
        .auth-alert-box {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 8px 12px;
          background: #f4f8f5;
          border: 1px solid #0f5f4f;
          color: #0f5f4f;
          font-size: 0.76rem;
          font-weight: 750;
          border-radius: 4px;
          line-height: 1.35;
        }
        .auth-card-footer {
          text-align: center;
          padding-top: 10px;
          border-top: 1px solid #e2ded4;
        }
        .auth-card-footer small {
          font-size: 0.68rem;
          color: #687067;
        }
        .auth-card-footer a {
          color: #172019;
          font-weight: 700;
          text-decoration: underline;
        }
        .auth-compact-footer {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 8px 24px;
          background: #ffffff;
          border-top: 1px solid #172019;
          font-size: 0.62rem;
          font-weight: 800;
          letter-spacing: 0.08em;
          color: #687067;
          flex-shrink: 0;
        }
        @media (max-width: 960px) {
          .auth-viewport-root {
            height: auto;
            max-height: none;
            overflow: visible;
          }
          .auth-split-container {
            grid-template-columns: 1fr;
            padding: 24px 0;
            gap: 28px;
          }
          .governance-triad-grid {
            grid-template-columns: 1fr;
          }
          .auth-compact-footer {
            flex-direction: column;
            gap: 4px;
            text-align: center;
          }
        }
      `}</style>
    </div>
  );
}
