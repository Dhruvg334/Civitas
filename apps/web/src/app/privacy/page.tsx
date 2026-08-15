"use client";

import { Footer, Nav, SectionLabel } from "@/components/site";

export default function Privacy() {
  return (
    <>
      <Nav />
      <main className="legal-main-shell">
        <div className="legal-header-block">
          <SectionLabel index="01">LEGAL & TRANSPARENCY</SectionLabel>
          <h1 className="legal-main-title">Privacy & Geolocation Policy</h1>
          <p className="legal-lead-text">
            Civitas is committed to strict data minimization. Location coordinates, media uploads, and resident identifiers are processed strictly to verify civic incidents and dispatch municipal crews.
          </p>
          <span className="last-updated-pill">Last Updated: August 2026 · PostGIS Compliance</span>
        </div>

        <div className="legal-sections-grid">
          <article className="legal-card">
            <span className="card-kicker">DATA HANDLING</span>
            <h2>01. Geolocation & Spatial Privacy</h2>
            <p>
              When you submit a report, GPS coordinates are used exclusively to query PostGIS spatial indexes, cluster nearby reports, and measure distance buffers to critical civic infrastructure (e.g. school gates, hospital crossings).
            </p>
            <p>
              Coordinates are never shared with advertising networks or third-party tracking brokers. You may decline browser GPS permission and provide an approximate landmark description instead.
            </p>
          </article>

          <article className="legal-card">
            <span className="card-kicker">EVIDENCE EXTRACTION</span>
            <h2>02. Media Uploads & EXIF Sanitization</h2>
            <p>
              Photos and video frames submitted by residents are analyzed by zero-shot computer vision models (CLIP) to identify physical infrastructure hazards (e.g., asphalt cracks, standing water, fallen timber).
            </p>
            <p>
              EXIF metadata containing personal device information or biometric identifiers is stripped before long-term storage in municipal records.
            </p>
          </article>

          <article className="legal-card">
            <span className="card-kicker">GOVERNANCE BOUNDARY</span>
            <h2>03. AI Processing & Human Review</h2>
            <p>
              Language models and agentic workflows are used to classify categories, retrieve relevant city policy playbooks, and draft work orders.
            </p>
            <p>
              High-impact decisions—including dispatching field repair crews, rerouting municipal departments, and closing incidents—require explicit human supervisor authorization.
            </p>
          </article>

          <article className="legal-card">
            <span className="card-kicker">RESIDENT RIGHTS</span>
            <h2>04. Your Data Rights & History Deletion</h2>
            <p>
              Residents can view their complete submission history, update notification preferences, and request deletion of historical civic reports from their profile dashboard.
            </p>
          </article>
        </div>
      </main>
      <Footer />

      <style jsx>{`
        .legal-main-shell {
          width: min(calc(100% - 40px), 980px);
          margin: 36px auto 100px;
        }
        .legal-header-block {
          padding-bottom: 28px;
          border-bottom: 2px solid #172019;
          margin-bottom: 36px;
        }
        .legal-main-title {
          font-size: clamp(2.4rem, 4.5vw, 3.8rem);
          font-family: Georgia, serif;
          margin: 8px 0 12px;
          color: #172019;
          line-height: 1;
        }
        .legal-lead-text {
          font-size: 1.05rem;
          color: #555e54;
          line-height: 1.6;
          margin: 0 0 16px;
        }
        .last-updated-pill {
          font-size: 0.68rem;
          font-weight: 850;
          background: #dce8dd;
          color: #0f5f4f;
          padding: 4px 10px;
          border-radius: 4px;
          display: inline-block;
        }
        .legal-sections-grid {
          display: flex;
          flex-direction: column;
          gap: 24px;
        }
        .legal-card {
          border: 1px solid #172019;
          background: #ffffff;
          box-shadow: 4px 4px 0 #172019;
          padding: 28px;
        }
        .card-kicker {
          font-size: 0.6rem;
          font-weight: 900;
          letter-spacing: 0.12em;
          color: #0f5f4f;
          display: block;
          margin-bottom: 6px;
        }
        .legal-card h2 {
          font-size: 1.35rem;
          font-family: Georgia, serif;
          margin: 0 0 12px;
          color: #172019;
        }
        .legal-card p {
          font-size: 0.9rem;
          color: #495248;
          line-height: 1.65;
          margin: 0 0 12px;
        }
        .legal-card p:last-child {
          margin-bottom: 0;
        }
      `}</style>
    </>
  );
}
