"use client";

import Link from "next/link";
import { Footer, Nav } from "@/components/site";
import { LandingExplorer } from "@/components/landing-explorer";
import { LiveEvidenceSandbox } from "@/components/live-evidence-sandbox";
import { ResolutionSlider } from "@/components/resolution-slider";

export default function Home() {
  return (
    <>
      <Nav />
      <main className="landing-main-shell">
        {/* FULLSCREEN HERO SECTION */}
        <section className="hero-fullscreen" aria-label="Civitas hero intro">
          <div className="hero-content-center">
            <div className="hero-kicker-pill">
              <span className="live-status-dot" />
              <span>EVIDENCE-BACKED CIVIC INCIDENT INTELLIGENCE</span>
            </div>

            <h1 className="hero-title">
              Turn chaotic civic reports into verified municipal action.
            </h1>

            <p className="hero-lead">
              Civitas connects multimodal citizen intake, PostGIS spatial clustering, deterministic ML models,
              and municipal policy retrieval into an audited LangGraph orchestration engine with human review checkpoints.
            </p>

            <div className="hero-cta-group">
              <Link className="button large hero-primary-btn" href="/workspace">
                Open Command Center →
              </Link>
              <Link className="outline large hero-secondary-btn" href="/demo-workflow">
                ⚡ Test Workflow Demo
              </Link>
            </div>

            <div className="hero-trust-bar">
              <span>POSTGIS 3.4 ENABLED</span>
              <span className="bullet-sep">·</span>
              <span>ZERO HALLUCINATED POLICIES</span>
              <span className="bullet-sep">·</span>
              <span>HUMAN-IN-THE-LOOP GATES</span>
            </div>
          </div>

          <div className="scroll-indicator" aria-hidden="true">
            <span>SCROLL TO EXPLORE WORKFLOW</span>
            <span className="arrow-down">↓</span>
          </div>
        </section>

        {/* METRICS COUNTER RIBBON */}
        <section className="metrics-ticker-ribbon" aria-label="System telemetry">
          <div className="metrics-container">
            <div className="metric-cell">
              <b className="metric-number">99.4%</b>
              <span className="metric-desc">Grounding Precision (Playbook-Backed)</span>
            </div>
            <div className="metric-cell">
              <b className="metric-number">0.0%</b>
              <span className="metric-desc">Hallucinated SLA Commitments</span>
            </div>
            <div className="metric-cell">
              <b className="metric-number">3.2x</b>
              <span className="metric-desc">Faster Duplicate Cluster Triage</span>
            </div>
            <div className="metric-cell">
              <b className="metric-number">100%</b>
              <span className="metric-desc">Supervisor Approval on Dispatches</span>
            </div>
          </div>
        </section>

        {/* LIVE EVIDENCE SANDBOX */}
        <section className="section-block live-sandbox-section" id="sandbox">
          <div className="section-header-tag">
            <span className="tag-index">INTERACTIVE</span>
            <h2>Try the Multimodal Intelligence Engine</h2>
            <p>
              See how Civitas separates raw citizen text from observable media facts and connects them to verified municipal playbooks.
            </p>
          </div>
          <LiveEvidenceSandbox />
        </section>

        {/* 3 CONNECTED CAPABILITIES EXPLORER */}
        <LandingExplorer />

        {/* BEFORE & AFTER RESOLUTION SHOWCASE */}
        <section className="section-block resolution-showcase-section" id="verification">
          <div className="section-header-tag">
            <span className="tag-index">VERIFICATION</span>
            <h2>Before / After Evidence Verification</h2>
            <p>
              Field crews submit resolution photos. The ML resolution engine compares before vs after imagery to prevent fraudulent ticket closures.
            </p>
          </div>

          <div className="resolution-card-wrap">
            <ResolutionSlider
              beforeLabel="Before: Main Pipeline Rupture (INC-0241)"
              afterLabel="After: Pipe Clamped & Asphalt Patched"
              classification="RESOLVED"
              resolvedEvidence={[
                "High-pressure water flow completely halted",
                "Subsurface trench backfilled and sealed with asphalt",
                "Road drainage restored; school gate clear",
              ]}
              remainingEvidence={["Minor surface moisture drying; no standing puddles"]}
            />
          </div>
        </section>

        {/* TRADITIONAL 311 VS CIVITAS ARCHITECTURAL COMPARISON */}
        <section className="section-block comparison-section">
          <div className="section-header-tag">
            <span className="tag-index">PHILOSOPHY</span>
            <h2>Traditional 311 CRM vs Civitas Intelligence</h2>
            <p>
              Why standard civic ticketing systems fail under pressure and how evidence-backed orchestration solves it.
            </p>
          </div>

          <div className="comparison-grid">
            <div className="comp-card traditional">
              <div className="comp-card-header">
                <span className="comp-badge bad">TRADITIONAL 311 SYSTEM</span>
                <h3>Naive Ticket Logging</h3>
              </div>
              <ul>
                <li>❌ 50 citizens report same water burst → creates 50 duplicate work orders.</li>
                <li>❌ Citizen descriptions are taken as blind instruction without media validation.</li>
                <li>❌ LLM chatbots fabricate delivery SLAs and hallucinate municipal repair commitments.</li>
                <li>❌ Tickets closed without verifiable image evidence or supervisor review.</li>
              </ul>
            </div>

            <div className="comp-card civitas">
              <div className="comp-card-header">
                <span className="comp-badge good">CIVITAS PLATFORM</span>
                <h3>Evidence-Backed Orchestration</h3>
              </div>
              <ul>
                <li>✓ <b>PostGIS Spatial Clustering:</b> 50 reports automatically converge into 1 master incident.</li>
                <li>✓ <b>Observable Evidence Split:</b> Separates citizen claims from verified photo pixels.</li>
                <li>✓ <b>Policy Grounding:</b> Every action cites retrieved municipal playbooks (e.g. PLAY-WATER-01).</li>
                <li>✓ <b>Human Authorization Gate:</b> High-impact work orders require supervisor approval.</li>
              </ul>
            </div>
          </div>
        </section>

        {/* FINAL CLOSING CALL-TO-ACTION */}
        <section className="closing-cta-section">
          <div className="closing-card">
            <span className="closing-kicker">READY TO DEPLOY</span>
            <h2 className="closing-title">Upgrade municipal operations with evidence intelligence.</h2>
            <p className="closing-desc">
              Explore the real-time command center, inspect LangGraph execution traces, or submit a test citizen report.
            </p>
            <div className="closing-buttons">
              <Link className="button large" href="/workspace">
                Open Command Center
              </Link>
              <Link className="outline large" href="/report">
                Submit Test Citizen Report
              </Link>
              <Link className="outline large" href="/docs">
                Read System Docs
              </Link>
            </div>
          </div>
        </section>
      </main>
      <Footer />

      <style jsx>{`
        .landing-main-shell {
          width: 100%;
          overflow-x: hidden;
        }
        .hero-fullscreen {
          min-height: calc(100vh - 74px);
          width: 100%;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          text-align: center;
          padding: 60px 20px 40px;
          background: radial-gradient(circle at 50% 20%, rgba(220, 232, 221, 0.4) 0%, rgba(251, 249, 244, 1) 70%);
          position: relative;
          box-sizing: border-box;
        }
        .hero-content-center {
          max-width: 960px;
          margin: 0 auto;
          display: flex;
          flex-direction: column;
          align-items: center;
        }
        .hero-kicker-pill {
          display: inline-flex;
          align-items: center;
          gap: 8px;
          padding: 6px 14px;
          border: 1px solid #172019;
          background: #ffffff;
          box-shadow: 2px 2px 0 #172019;
          font-size: 0.68rem;
          font-weight: 900;
          letter-spacing: 0.1em;
          color: #0f5f4f;
          border-radius: 4px;
          margin-bottom: 24px;
        }
        .live-status-dot {
          width: 7px;
          height: 7px;
          border-radius: 50%;
          background: #10b981;
          box-shadow: 0 0 6px #10b981;
        }
        .hero-title {
          font-size: clamp(2.8rem, 6.2vw, 5.2rem);
          line-height: 0.94;
          font-family: Georgia, serif;
          color: #172019;
          margin: 0 0 20px;
          letter-spacing: -0.02em;
          max-width: 880px;
        }
        .hero-lead {
          font-size: clamp(1rem, 1.8vw, 1.22rem);
          line-height: 1.6;
          color: #495248;
          max-width: 740px;
          margin: 0 0 32px;
        }
        .hero-cta-group {
          display: flex;
          gap: 16px;
          flex-wrap: wrap;
          justify-content: center;
          margin-bottom: 36px;
        }
        .hero-primary-btn {
          box-shadow: 4px 4px 0 #172019;
          font-size: 0.95rem !important;
          padding: 14px 28px !important;
        }
        .hero-secondary-btn {
          box-shadow: 4px 4px 0 #172019;
          font-size: 0.95rem !important;
          padding: 14px 28px !important;
          background: #ffffff;
        }
        .hero-trust-bar {
          display: flex;
          align-items: center;
          gap: 12px;
          font-size: 0.68rem;
          font-weight: 850;
          letter-spacing: 0.1em;
          color: #687067;
          flex-wrap: wrap;
          justify-content: center;
        }
        .bullet-sep {
          color: #0f5f4f;
        }
        .scroll-indicator {
          margin-top: auto;
          padding-top: 30px;
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 4px;
          font-size: 0.62rem;
          font-weight: 850;
          letter-spacing: 0.12em;
          color: #687067;
        }
        .arrow-down {
          font-size: 1rem;
          animation: bounce 1.8s infinite;
        }
        .metrics-ticker-ribbon {
          width: 100%;
          border-top: 1px solid #172019;
          border-bottom: 1px solid #172019;
          background: #172019;
          color: #ffffff;
          padding: 24px 20px;
        }
        .metrics-container {
          width: min(calc(100% - 40px), 1180px);
          margin: 0 auto;
          display: grid;
          grid-template-columns: repeat(4, 1fr);
          gap: 24px;
        }
        .metric-cell {
          display: flex;
          flex-direction: column;
          gap: 4px;
          border-left: 1px solid #333f36;
          padding-left: 18px;
        }
        .metric-cell:first-child {
          border-left: 0;
          padding-left: 0;
        }
        .metric-number {
          font-size: 2.2rem;
          font-family: Georgia, serif;
          color: #e84d7a;
          line-height: 1;
        }
        .metric-desc {
          font-size: 0.75rem;
          color: #9da99e;
          font-weight: 700;
          line-height: 1.35;
        }
        .section-block {
          width: min(calc(100% - 40px), 1180px);
          margin: 80px auto;
        }
        .section-header-tag {
          margin-bottom: 32px;
        }
        .tag-index {
          font-size: 0.65rem;
          font-weight: 900;
          letter-spacing: 0.14em;
          color: #0f5f4f;
          display: block;
          margin-bottom: 6px;
        }
        .section-header-tag h2 {
          font-size: clamp(2rem, 3.8vw, 3.2rem);
          font-family: Georgia, serif;
          color: #172019;
          margin: 0 0 10px;
          line-height: 1;
        }
        .section-header-tag p {
          font-size: 1rem;
          color: #555e54;
          margin: 0;
          max-width: 680px;
          line-height: 1.55;
        }
        .resolution-card-wrap {
          border: 2px solid #172019;
          background: #ffffff;
          box-shadow: 6px 6px 0 #172019;
          padding: 24px;
        }
        .comparison-grid {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 28px;
        }
        .comp-card {
          border: 2px solid #172019;
          padding: 28px;
          border-radius: 6px;
        }
        .comp-card.traditional {
          background: #fff8f8;
          box-shadow: 4px 4px 0 #c23358;
        }
        .comp-card.civitas {
          background: #f4f8f5;
          box-shadow: 4px 4px 0 #0f5f4f;
        }
        .comp-card-header {
          margin-bottom: 18px;
        }
        .comp-badge {
          font-size: 0.62rem;
          font-weight: 900;
          letter-spacing: 0.1em;
          padding: 3px 8px;
          border-radius: 3px;
          display: inline-block;
          margin-bottom: 6px;
        }
        .comp-badge.bad {
          background: #fbe6eb;
          color: #c23358;
        }
        .comp-badge.good {
          background: #dce8dd;
          color: #0f5f4f;
        }
        .comp-card h3 {
          font-size: 1.3rem;
          font-family: Georgia, serif;
          margin: 0;
          color: #172019;
        }
        .comp-card ul {
          margin: 0;
          padding: 0;
          list-style: none;
          display: flex;
          flex-direction: column;
          gap: 12px;
        }
        .comp-card li {
          font-size: 0.88rem;
          line-height: 1.5;
          color: #333f36;
        }
        .closing-cta-section {
          width: min(calc(100% - 40px), 1180px);
          margin: 80px auto 100px;
        }
        .closing-card {
          border: 2px solid #172019;
          background: #172019;
          color: #ffffff;
          box-shadow: 8px 8px 0 #0f5f4f;
          padding: 48px;
          text-align: center;
          display: flex;
          flex-direction: column;
          align-items: center;
        }
        .closing-kicker {
          font-size: 0.65rem;
          font-weight: 900;
          letter-spacing: 0.14em;
          color: #dce8dd;
          margin-bottom: 8px;
        }
        .closing-title {
          font-size: clamp(2.2rem, 4vw, 3.4rem);
          font-family: Georgia, serif;
          color: #ffffff;
          margin: 0 0 14px;
          line-height: 1.05;
          max-width: 780px;
        }
        .closing-desc {
          font-size: 1rem;
          color: #9da99e;
          max-width: 620px;
          margin: 0 0 28px;
          line-height: 1.55;
        }
        .closing-buttons {
          display: flex;
          gap: 14px;
          flex-wrap: wrap;
          justify-content: center;
        }
        .closing-buttons :global(.button) {
          box-shadow: 3px 3px 0 #0f5f4f;
        }
        .closing-buttons :global(.outline) {
          background: #232d25;
          color: #ffffff;
          border-color: #ffffff;
          box-shadow: 3px 3px 0 #0f5f4f;
        }
        @keyframes bounce {
          0%, 100% { transform: translateY(0); }
          50% { transform: translateY(4px); }
        }
        @media (max-width: 900px) {
          .metrics-container {
            grid-template-columns: 1fr 1fr;
          }
          .comparison-grid {
            grid-template-columns: 1fr;
          }
        }
        @media (max-width: 600px) {
          .metrics-container {
            grid-template-columns: 1fr;
          }
          .closing-card {
            padding: 32px 20px;
          }
        }
      `}</style>
    </>
  );
}
