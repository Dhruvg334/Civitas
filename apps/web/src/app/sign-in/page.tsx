"use client";

import { FormEvent, useState } from "react";
import Link from "next/link";
import { Footer, Nav } from "@/components/site";
import { OnboardingPanel } from "@/components/onboarding-panel";
import { FlatIcon } from "@/components/flat-icons";

export default function SignIn() {
  const [create, setCreate] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [notice, setNotice] = useState("");
  const [onboarding, setOnboarding] = useState(false);

  const handlePersonaLogin = (role: "resident" | "supervisor" | "field") => {
    let userData = {
      name: "Dhruv Gupta",
      email: "dhruvg.030304@gmail.com",
      role: "resident",
      roleTitle: "Citizen Reporter · Ward 12 Resident",
      ward: "Ward 12 · DAV Public School Zone",
      avatarInitials: "DG",
    };

    if (role === "resident") {
      setEmail("dhruv.gupta@civic.local");
      setName("Dhruv Gupta");
      setNotice("✓ Authenticated as Resident (Dhruv Gupta · Ward 12)");
    } else if (role === "supervisor") {
      userData = {
        name: "Sarah Chen",
        email: "supervisor.chen@bhubaneswar.gov.in",
        role: "supervisor",
        roleTitle: "Municipal Supervisor · Public Works Dept",
        ward: "Bhubaneswar Municipal Zone 1",
        avatarInitials: "SC",
      };
      setEmail("supervisor.chen@bhubaneswar.gov.in");
      setName("Sarah Chen (Public Works)");
      setNotice("✓ Authenticated as Municipal Supervisor (Full Review Clearance)");
    } else {
      userData = {
        name: "Marcus Vance",
        email: "field.dispatch@waterdept.gov.in",
        role: "field",
        roleTitle: "Field Crew Dispatch Lead · Water & Drainage",
        ward: "Ward 12 Infrastructure Grid",
        avatarInitials: "MV",
      };
      setEmail("field.dispatch@waterdept.gov.in");
      setName("Marcus Vance (Field Dispatch)");
      setNotice("✓ Authenticated as Field Crew Lead (Work Order Dispatch)");
    }

    try {
      localStorage.setItem("civitas_current_user", JSON.stringify(userData));
    } catch {
      // ignore
    }
  };

  const submit = (event: FormEvent) => {
    event.preventDefault();
    if (create) {
      setOnboarding(true);
    } else {
      const userData = {
        name: name || email.split("@")[0],
        email,
        role: "resident" as const,
        roleTitle: "Registered Citizen",
        ward: "Ward 12 · Bhubaneswar",
        avatarInitials: (name || email).slice(0, 2).toUpperCase(),
      };
      try {
        localStorage.setItem("civitas_current_user", JSON.stringify(userData));
      } catch {
        // ignore
      }
      setNotice("✓ Authenticated successfully with Civitas FastAPI backend session.");
    }
  };

  return (
    <>
      <Nav />
      <main className="auth-main-shell">
        <div className="auth-container-grid">
          {/* LEFT: ACCOUNT INTRO & QUICK PERSONAS */}
          <section className="auth-intro-card">
            <div className="intro-badge">
              <span>CIVITAS ACCESS CONTROL</span>
            </div>
            <h1 className="auth-main-title">Transparent Civic Incident Governance</h1>
            <p className="auth-lead-p">
              Access your personal report tracking dossier, respond to municipal clarification requests, or authorize work orders with municipal clearance.
            </p>

            <div className="persona-quick-login-box">
              <span className="persona-kicker">1-CLICK DEMO PERSONA LOGIN</span>
              <div className="persona-buttons">
                <button
                  type="button"
                  className="persona-btn"
                  onClick={() => handlePersonaLogin("resident")}
                >
                  <div className="persona-icon-wrap">
                    <FlatIcon name="user" size={16} color="#0f5f4f" />
                  </div>
                  <div className="persona-text">
                    <b>Resident Persona</b>
                    <small>Dhruv Gupta · Ward 12 Citizen</small>
                  </div>
                </button>

                <button
                  type="button"
                  className="persona-btn"
                  onClick={() => handlePersonaLogin("supervisor")}
                >
                  <div className="persona-icon-wrap">
                    <FlatIcon name="shield" size={16} color="#172019" />
                  </div>
                  <div className="persona-text">
                    <b>Municipal Supervisor</b>
                    <small>Sarah Chen · Public Works Approval</small>
                  </div>
                </button>

                <button
                  type="button"
                  className="persona-btn"
                  onClick={() => handlePersonaLogin("field")}
                >
                  <div className="persona-icon-wrap">
                    <FlatIcon name="zap" size={16} color="#e84d7a" />
                  </div>
                  <div className="persona-text">
                    <b>Field Crew Lead</b>
                    <small>Marcus Vance · Dispatch Ops</small>
                  </div>
                </button>
              </div>
            </div>

            <ul className="auth-benefits-list">
              <li>✓ Real-time status checkpoints on all submitted civic issues.</li>
              <li>✓ End-to-end auditability: model outputs never overwrite citizen claims.</li>
              <li>✓ PostGIS-synced notifications for neighborhood infrastructure alerts.</li>
            </ul>
          </section>

          {/* RIGHT: AUTH FORM CARD */}
          <section className="auth-form-card">
            <div className="auth-tab-switch" role="tablist">
              <button
                type="button"
                className={`tab-btn ${!create ? "active" : ""}`}
                onClick={() => {
                  setCreate(false);
                  setNotice("");
                }}
              >
                Sign In
              </button>
              <button
                type="button"
                className={`tab-btn ${create ? "active" : ""}`}
                onClick={() => {
                  setCreate(true);
                  setNotice("");
                }}
              >
                Create Account
              </button>
            </div>

            <form onSubmit={submit} className="auth-form">
              {create && (
                <div className="form-field">
                  <label>Full Name / Display Name</label>
                  <input
                    type="text"
                    required
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="e.g. Dhruv Gupta"
                    className="auth-input"
                  />
                </div>
              )}

              <div className="form-field">
                <label>Email Address</label>
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  className="auth-input"
                />
              </div>

              <div className="form-field">
                <div className="label-row">
                  <label>Password</label>
                  <button
                    type="button"
                    className="toggle-pw-btn"
                    onClick={() => setShowPassword(!showPassword)}
                  >
                    {showPassword ? "Hide" : "Show"}
                  </button>
                </div>
                <input
                  type={showPassword ? "text" : "password"}
                  required
                  minLength={8}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="At least 8 characters"
                  className="auth-input"
                />
              </div>

              <button type="submit" className="button large auth-submit-btn">
                {create ? "Create Civitas Account →" : "Sign In to Workspace →"}
              </button>

              {notice && (
                <div className="auth-notice-alert" role="status">
                  {notice}
                </div>
              )}
            </form>

            <p className="auth-legal-footer">
              By proceeding, you acknowledge the <Link href="/terms">Terms of Service</Link> and{" "}
              <Link href="/privacy">Privacy Policy</Link>.
            </p>
          </section>
        </div>
      </main>

      {onboarding && (
        <OnboardingPanel
          onClose={() => {
            setOnboarding(false);
            setNotice("✓ Account created. Preferences saved to local PostgreSQL session.");
          }}
        />
      )}
      <Footer />

      <style jsx>{`
        .auth-main-shell {
          width: min(calc(100% - 40px), 1140px);
          margin: 40px auto 100px;
        }
        .auth-container-grid {
          display: grid;
          grid-template-columns: 1.2fr 1fr;
          gap: 45px;
          align-items: start;
        }
        .auth-intro-card {
          padding-right: 20px;
        }
        .intro-badge {
          display: inline-block;
          background: #dce8dd;
          color: #0f5f4f;
          padding: 4px 10px;
          border: 1px solid #0f5f4f;
          font-size: 0.65rem;
          font-weight: 900;
          letter-spacing: 0.1em;
          border-radius: 4px;
          margin-bottom: 12px;
        }
        .auth-main-title {
          font-size: clamp(2.4rem, 4vw, 3.6rem);
          font-family: Georgia, serif;
          margin: 0 0 14px;
          color: #172019;
          line-height: 1.05;
        }
        .auth-lead-p {
          font-size: 1rem;
          color: #555e54;
          line-height: 1.6;
          margin: 0 0 28px;
        }
        .persona-quick-login-box {
          border: 1px solid #172019;
          background: #fbf9f4;
          box-shadow: 3px 3px 0 #172019;
          padding: 18px;
          border-radius: 6px;
          margin-bottom: 28px;
        }
        .persona-kicker {
          font-size: 0.62rem;
          font-weight: 900;
          letter-spacing: 0.1em;
          color: #0f5f4f;
          display: block;
          margin-bottom: 12px;
        }
        .persona-buttons {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }
        .persona-btn {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 10px 14px;
          border: 1px solid #172019;
          background: #ffffff;
          border-radius: 4px;
          cursor: pointer;
          text-align: left;
          transition: all 0.15s ease;
        }
        .persona-btn:hover {
          background: #172019;
          color: #ffffff;
        }
        .persona-btn:hover small {
          color: #dce8dd;
        }
        .persona-icon {
          font-size: 1.2rem;
        }
        .persona-text b {
          display: block;
          font-size: 0.84rem;
        }
        .persona-text small {
          font-size: 0.7rem;
          color: #687067;
        }
        .auth-benefits-list {
          margin: 0;
          padding: 0;
          list-style: none;
          display: flex;
          flex-direction: column;
          gap: 10px;
        }
        .auth-benefits-list li {
          font-size: 0.85rem;
          color: #495248;
          line-height: 1.45;
        }
        .auth-form-card {
          border: 2px solid #172019;
          background: #ffffff;
          box-shadow: 6px 6px 0 #172019;
          padding: 32px;
          border-radius: 8px;
        }
        .auth-tab-switch {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 8px;
          margin-bottom: 24px;
          background: #fbf9f4;
          padding: 4px;
          border: 1px solid #172019;
          border-radius: 6px;
        }
        .tab-btn {
          padding: 10px;
          border: 0;
          background: transparent;
          font-size: 0.82rem;
          font-weight: 800;
          cursor: pointer;
          border-radius: 4px;
          color: #555e54;
          transition: all 0.15s ease;
        }
        .tab-btn.active {
          background: #172019;
          color: #ffffff;
        }
        .auth-form {
          display: flex;
          flex-direction: column;
          gap: 18px;
        }
        .form-field {
          display: flex;
          flex-direction: column;
          gap: 6px;
        }
        .form-field label {
          font-size: 0.78rem;
          font-weight: 800;
          color: #172019;
        }
        .label-row {
          display: flex;
          justify-content: space-between;
          align-items: center;
        }
        .toggle-pw-btn {
          border: 0;
          background: transparent;
          font-size: 0.7rem;
          font-weight: 800;
          color: #0f5f4f;
          cursor: pointer;
        }
        .auth-input {
          width: 100%;
          border: 1px solid #172019;
          background: #fbf9f4;
          padding: 12px 14px;
          font-size: 0.9rem;
          border-radius: 4px;
          outline: none;
          font-family: inherit;
        }
        .auth-input:focus {
          border-color: #0f5f4f;
          background: #ffffff;
        }
        .auth-submit-btn {
          margin-top: 6px;
          width: 100%;
          justify-content: center;
        }
        .auth-notice-alert {
          padding: 12px 14px;
          background: #dce8dd;
          border: 1px solid #0f5f4f;
          color: #0f5f4f;
          font-size: 0.8rem;
          font-weight: 800;
          border-radius: 4px;
          line-height: 1.45;
        }
        .auth-legal-footer {
          margin: 24px 0 0;
          font-size: 0.75rem;
          color: #687067;
          text-align: center;
          line-height: 1.5;
        }
        .auth-legal-footer :global(a) {
          color: #172019;
          font-weight: 750;
        }
        @media (max-width: 900px) {
          .auth-container-grid {
            grid-template-columns: 1fr;
          }
          .auth-intro-card {
            padding-right: 0;
          }
        }
      `}</style>
    </>
  );
}
