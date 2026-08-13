"use client";

import { useState } from "react";
import Link from "next/link";
import { Footer, Nav, Status } from "@/components/site";

const history = [
  [
    "REPORT-103",
    "Water on road near school",
    "Grouped into INC-0241",
    "P1 High",
    "Today",
    "good",
  ],
  [
    "REPORT-097",
    "Streetlight outage near crosswalk",
    "Awaiting clarification",
    "P3 Low",
    "2 days ago",
    "warn",
  ],
  [
    "REPORT-088",
    "Blocked pedestrian sidewalk",
    "Sent to Public Works",
    "P2 Medium",
    "6 days ago",
    "good",
  ],
];

export default function Profile() {
  const [activeTab, setActiveTab] = useState("overview");
  const [displayName, setDisplayName] = useState("Dhruv Gupta");
  const [email, setEmail] = useState("dhruvg.030304@gmail.com");
  const [ward, setWard] = useState("Ward 12 · Bhubaneswar");
  const [notify, setNotify] = useState(true);
  const [savedNotice, setSavedNotice] = useState("");

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    setSavedNotice("Profile preferences updated successfully.");
    setTimeout(() => setSavedNotice(""), 4000);
  };

  return (
    <>
      <Nav />
      <main className="profile-shell">
        {/* SUBNAV TABS */}
        <nav className="profile-subnav" aria-label="Profile sections">
          <button
            className={`subnav-btn ${activeTab === "overview" ? "active" : ""}`}
            onClick={() => setActiveTab("overview")}
          >
            Overview & Activity
          </button>
          <button
            className={`subnav-btn ${activeTab === "history" ? "active" : ""}`}
            onClick={() => setActiveTab("history")}
          >
            Report History (3)
          </button>
          <button
            className={`subnav-btn ${activeTab === "preferences" ? "active" : ""}`}
            onClick={() => setActiveTab("preferences")}
          >
            Account Preferences
          </button>
        </nav>

        {/* PROFILE HEADER CARD */}
        <section className="profile-header-card">
          <div className="profile-avatar">DG</div>
          <div className="profile-intro">
            <span className="workspace-kicker">RESIDENT CIVIC PROFILE</span>
            <h1>Stay connected to the reports you start.</h1>
            <p>
              Manage how Civitas contacts you, select your primary ward, and review transparent status updates
              for every civic incident you submit.
            </p>
            <div className="profile-header-actions">
              <Link className="button" href="/sign-in">
                Sign in or create account
              </Link>
              <Status tone="warn">SIGNED_OUT_PREVIEW</Status>
              <span className="ward-badge">{ward}</span>
            </div>
          </div>
        </section>

        {/* OVERVIEW STATS */}
        <section className="profile-stats-grid">
          <article className="stat-card">
            <span>REPORTS SUBMITTED</span>
            <b>03 Reports</b>
            <small>Active in Bhubaneswar preview</small>
          </article>

          <article className="stat-card">
            <span>ACTION REQUIRED</span>
            <b>01 Clarification</b>
            <small>Response requested on REPORT-097</small>
          </article>

          <article className="stat-card">
            <span>WORK ORDERS ISSUED</span>
            <b>02 Executed</b>
            <small>Assigned to Water Dept & Public Works</small>
          </article>
        </section>

        {activeTab === "overview" || activeTab === "history" ? (
          <section className="history-section">
            <div className="history-heading">
              <div>
                <span className="section-kicker">INCIDENT TIMELINE</span>
                <h2>Recent Civic Activity</h2>
              </div>
              <span className="history-count">3 total reports</span>
            </div>

            <div className="history-list-box">
              {history.map(([id, title, status, priority, date, tone]) => (
                <article className="history-row" key={id}>
                  <div className="row-col-id">
                    <span className="id-tag">{id}</span>
                  </div>
                  <div className="row-col-title">
                    <b>{title}</b>
                    <small>Submitted {date}</small>
                  </div>
                  <div className="row-col-status">
                    <Status tone={tone as any}>{status}</Status>
                  </div>
                  <div className="row-col-prio">
                    <span className="prio-tag">{priority}</span>
                  </div>
                </article>
              ))}
            </div>
          </section>
        ) : null}

        {activeTab === "preferences" || activeTab === "overview" ? (
          <section className="profile-settings-box">
            <div className="settings-header">
              <span className="section-kicker">ACCOUNT SETTINGS</span>
              <h2>Profile & Notification Preferences</h2>
            </div>

            <form onSubmit={handleSave} className="settings-form">
              <div className="form-grid">
                <label className="form-label">
                  Display Name
                  <input
                    type="text"
                    value={displayName}
                    onChange={(e) => setDisplayName(e.target.value)}
                    required
                  />
                </label>

                <label className="form-label">
                  Email Address
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                  />
                </label>

                <label className="form-label">
                  Primary Municipal Ward
                  <select
                    value={ward}
                    onChange={(e) => setWard(e.target.value)}
                  >
                    <option value="Ward 12 · Bhubaneswar">Ward 12 · Bhubaneswar (Demo)</option>
                    <option value="Ward 08 · Bhubaneswar">Ward 08 · Bhubaneswar</option>
                    <option value="Ward 15 · Bhubaneswar">Ward 15 · Bhubaneswar</option>
                  </select>
                </label>

                <label className="form-label checkbox-label">
                  <input
                    type="checkbox"
                    checked={notify}
                    onChange={(e) => setNotify(e.target.checked)}
                  />
                  <span>Receive email notifications for clarification requests and status closures</span>
                </label>
              </div>

              <div className="form-actions-row">
                <button type="submit" className="button small">
                  Save Preferences
                </button>
                {savedNotice && <span className="save-notice">{savedNotice}</span>}
              </div>
            </form>
          </section>
        ) : null}
      </main>
      <Footer />

      <style jsx>{`
        .profile-shell {
          width: min(calc(100% - 40px), 1100px);
          margin: 40px auto 90px;
        }
        .profile-subnav {
          display: flex;
          gap: 0;
          border: 1px solid #172019;
          background: #fbf9f4;
          width: max-content;
          margin-bottom: 32px;
        }
        .subnav-btn {
          padding: 10px 18px;
          border: 0;
          border-right: 1px solid #172019;
          background: transparent;
          font-size: 0.78rem;
          font-weight: 800;
          cursor: pointer;
          transition: background 0.15s ease, color 0.15s ease;
        }
        .subnav-btn:last-child {
          border-right: 0;
        }
        .subnav-btn.active {
          background: #172019;
          color: #ffffff;
        }
        .profile-header-card {
          display: grid;
          grid-template-columns: 90px minmax(0, 1fr);
          gap: 28px;
          align-items: start;
          padding-bottom: 35px;
          border-bottom: 2px solid #172019;
        }
        .profile-avatar {
          width: 86px;
          height: 86px;
          border: 2px solid #172019;
          background: #e84d7a;
          color: #ffffff;
          display: grid;
          place-items: center;
          font-family: Georgia, serif;
          font-size: 2.2rem;
          font-weight: 700;
          box-shadow: 4px 4px 0 #172019;
        }
        .profile-intro h1 {
          font-size: clamp(2.4rem, 4.2vw, 3.8rem);
          line-height: 0.95;
          margin: 6px 0 12px;
          font-family: Georgia, serif;
        }
        .profile-intro p {
          max-width: 680px;
          color: #495248;
          font-size: 0.95rem;
          line-height: 1.6;
          margin-bottom: 16px;
        }
        .profile-header-actions {
          display: flex;
          align-items: center;
          gap: 12px;
        }
        .ward-badge {
          padding: 4px 8px;
          border: 1px solid #172019;
          background: #fbf9f4;
          font-size: 0.65rem;
          font-weight: 800;
        }
        .profile-stats-grid {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          margin: 32px 0 45px;
          border: 1px solid #172019;
          background: #ffffff;
          box-shadow: 4px 4px 0 #172019;
        }
        .stat-card {
          padding: 20px 22px;
          border-right: 1px solid #e2ded4;
          display: flex;
          flex-direction: column;
          gap: 6px;
        }
        .stat-card:last-child {
          border-right: 0;
        }
        .stat-card span {
          font-size: 0.6rem;
          font-weight: 900;
          letter-spacing: 0.1em;
          color: #0f5f4f;
        }
        .stat-card b {
          font-size: 1.6rem;
          font-family: Georgia, serif;
          color: #172019;
        }
        .stat-card small {
          font-size: 0.72rem;
          color: #687067;
        }
        .history-section {
          margin-bottom: 45px;
        }
        .history-heading {
          display: flex;
          justify-content: space-between;
          align-items: flex-end;
          margin-bottom: 16px;
        }
        .history-heading h2 {
          font-size: 1.4rem;
          margin: 4px 0 0;
          font-weight: 850;
        }
        .history-count {
          font-size: 0.75rem;
          font-weight: 750;
          color: #687067;
        }
        .history-list-box {
          border: 1px solid #172019;
          background: #ffffff;
          box-shadow: 4px 4px 0 #172019;
        }
        .history-row {
          display: grid;
          grid-template-columns: 110px 1fr auto 100px;
          gap: 20px;
          align-items: center;
          padding: 16px 20px;
          border-bottom: 1px solid #e2ded4;
        }
        .history-row:last-child {
          border-bottom: 0;
        }
        .id-tag {
          font-size: 0.68rem;
          font-weight: 900;
          color: #e84d7a;
        }
        .row-col-title b {
          display: block;
          font-size: 0.9rem;
          color: #172019;
        }
        .row-col-title small {
          font-size: 0.7rem;
          color: #687067;
        }
        .prio-tag {
          font-size: 0.65rem;
          font-weight: 850;
          padding: 3px 7px;
          border: 1px solid #172019;
          background: #fbf9f4;
        }
        .profile-settings-box {
          padding: 32px;
          border: 1px solid #172019;
          background: #ffffff;
          box-shadow: 4px 4px 0 #172019;
          margin-bottom: 45px;
        }
        .settings-header h2 {
          font-size: 1.4rem;
          margin: 4px 0 20px;
          font-weight: 850;
        }
        .form-grid {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 20px;
        }
        .form-label {
          display: flex;
          flex-direction: column;
          gap: 8px;
          font-size: 0.78rem;
          font-weight: 800;
          color: #172019;
        }
        .form-label input,
        .form-label select {
          padding: 11px 13px;
          border: 1px solid #172019;
          background: #fbf9f4;
          font-size: 0.88rem;
        }
        .checkbox-label {
          grid-column: 1 / -1;
          flex-direction: row;
          align-items: center;
          gap: 10px;
          font-weight: 700;
          font-size: 0.82rem;
        }
        .checkbox-label input {
          width: 18px;
          height: 18px;
        }
        .form-actions-row {
          display: flex;
          align-items: center;
          gap: 16px;
          margin-top: 24px;
        }
        .save-notice {
          color: #0f5f4f;
          font-size: 0.8rem;
          font-weight: 800;
        }
        @media (max-width: 760px) {
          .profile-header-card {
            grid-template-columns: 1fr;
          }
          .profile-stats-grid {
            grid-template-columns: 1fr;
          }
          .history-row {
            grid-template-columns: 1fr;
            gap: 8px;
          }
          .form-grid {
            grid-template-columns: 1fr;
          }
        }
      `}</style>
    </>
  );
}
