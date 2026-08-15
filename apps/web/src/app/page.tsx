"use client";

import Link from "next/link";
import { Footer, Nav } from "@/components/site";
import { LandingExplorer } from "@/components/landing-explorer";
import { LiveEvidenceSandbox } from "@/components/live-evidence-sandbox";
import { ResolutionSlider } from "@/components/resolution-slider";
import { FlatIcon } from "@/components/flat-icons";

export default function Home() {
  return (
    <>
      <Nav />
      <main className="landing-main-shell">
        {/* HERO SECTION */}
        <section className="hero-fullscreen" aria-label="Civitas hero intro">
          <div className="hero-content-center">
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
              <Link className="outline large hero-secondary-btn" href="/report">
                Submit Citizen Report
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
            <div className="tag-row">
              <span className="tag-index">01</span>
              <span className="section-kicker">MULTIMODAL INTELLIGENCE</span>
            </div>
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
            <div className="tag-row">
              <span className="tag-index">03</span>
              <span className="section-kicker">VERIFICATION</span>
            </div>
            <h2>Before / After Evidence Verification</h2>
            <p>
              Field crews submit resolution photos. The ML resolution engine compares before vs after imagery to prevent fraudulent ticket closures.
            </p>
          </div>

          <div className="resolution-card-wrap">
            <ResolutionSlider
              beforeLabel="Before: Main Pipeline Rupture (INC-0241)"
              afterLabel="After: Clamped Pipe & Backfilled Asphalt"
              classification="RESOLVED"
              resolvedEvidence={[
                "Subsurface high-pressure water flow completely halted",
                "Ductile iron repair collar secured and pressure-tested",
                "Excavated trench backfilled and sealed with hot-mix asphalt",
                "Pedestrian crossing outside DAV Public School unobstructed",
              ]}
              remainingEvidence={["Minor surface moisture drying on road shoulder; zero standing puddles"]}
            />
          </div>
        </section>

        {/* TRADITIONAL 311 VS CIVITAS ARCHITECTURAL COMPARISON */}
        <section className="section-block comparison-section">
          <div className="section-header-tag">
            <div className="tag-row">
              <span className="tag-index">04</span>
              <span className="section-kicker">PHILOSOPHY</span>
            </div>
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
              <ul className="comp-list">
                <li>
                  <span className="icon-cross">✕</span>
                  <span>50 citizens report same water burst → creates 50 duplicate work orders.</span>
                </li>
                <li>
                  <span className="icon-cross">✕</span>
                  <span>Citizen descriptions are taken as blind instruction without media validation.</span>
                </li>
                <li>
                  <span className="icon-cross">✕</span>
                  <span>LLM chatbots fabricate delivery SLAs and hallucinate municipal repair commitments.</span>
                </li>
                <li>
                  <span className="icon-cross">✕</span>
                  <span>Tickets closed without verifiable image evidence or supervisor review.</span>
                </li>
              </ul>
            </div>

            <div className="comp-card civitas">
              <div className="comp-card-header">
                <span className="comp-badge good">CIVITAS PLATFORM</span>
                <h3>Evidence-Backed Orchestration</h3>
              </div>
              <ul className="comp-list">
                <li>
                  <FlatIcon name="check" size={16} color="#0f5f4f" />
                  <span>PostGIS 3.4 clusters 50 reports into a single consolidated incident dossier.</span>
                </li>
                <li>
                  <FlatIcon name="check" size={16} color="#0f5f4f" />
                  <span>Strict separation between observable evidence, claims, and inferences.</span>
                </li>
                <li>
                  <FlatIcon name="check" size={16} color="#0f5f4f" />
                  <span>Every action grounded in verified municipal playbooks (e.g. PLAY-WATER-01).</span>
                </li>
                <li>
                  <FlatIcon name="check" size={16} color="#0f5f4f" />
                  <span>Mandatory human-in-the-loop review for high-impact dispatch and closure.</span>
                </li>
              </ul>
            </div>
          </div>
        </section>
      </main>
      <Footer />

      <style jsx>{`
        .landing-main-shell {
          width: 100%;
          min-height: 100vh;
        }
        .hero-fullscreen {
          min-height: calc(100vh - 74px);
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 60px 20px;
          border-bottom: 2px solid #172019;
          background: #fbf9f4;
          text-align: center;
        }
        .hero-content-center {
          width: min(calc(100% - 40px), 940px);
          margin: 0 auto;
          display: flex;
          flex-direction: column;
          align-items: center;
        }
        .hero-title {
          font-size: clamp(2.8rem, 5.5vw, 4.8rem);
          font-family: Georgia, serif;
          margin: 0 0 20px;
          line-height: 1.02;
          color: #172019;
          letter-spacing: -0.02em;
        }
        .hero-lead {
          font-size: clamp(1.05rem, 2vw, 1.25rem);
          color: #495248;
          line-height: 1.6;
          margin: 0 0 36px;
          max-width: 800px;
        }
        .hero-cta-group {
          display: flex;
          gap: 16px;
          justify-content: center;
          margin-bottom: 36px;
          flex-wrap: wrap;
        }
        .hero-primary-btn {
          box-shadow: 4px 4px 0 #172019;
        }
        .hero-secondary-btn {
          background: #ffffff;
          box-shadow: 4px 4px 0 #172019;
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
        .metrics-ticker-ribbon {
          border-bottom: 1px solid #172019;
          background: #172019;
          color: #ffffff;
          padding: 24px 0;
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
          border-left: 1px solid #334035;
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
          font-size: 0.72rem;
          color: #dce8dd;
          line-height: 1.35;
          font-weight: 600;
        }
        .section-block {
          width: min(calc(100% - 40px), 1180px);
          margin: 80px auto;
        }
        .section-header-tag {
          margin-bottom: 32px;
        }
        .tag-row {
          display: flex;
          align-items: center;
          gap: 8px;
          margin-bottom: 8px;
        }
        .tag-index {
          font-size: 0.65rem;
          font-weight: 900;
          padding: 2px 6px;
          border: 1px solid #172019;
          background: #172019;
          color: #ffffff;
          border-radius: 3px;
        }
        .section-kicker {
          font-size: 0.68rem;
          font-weight: 900;
          letter-spacing: 0.12em;
          color: #0f5f4f;
        }
        .section-header-tag h2 {
          font-size: clamp(2rem, 3.8vw, 3.2rem);
          font-family: Georgia, serif;
          margin: 6px 0 10px;
          color: #172019;
          line-height: 1.05;
        }
        .section-header-tag p {
          font-size: 1rem;
          color: #555e54;
          max-width: 680px;
          margin: 0;
          line-height: 1.55;
        }
        .resolution-card-wrap {
          margin-top: 24px;
        }
        .comparison-grid {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 28px;
        }
        .comp-card {
          border: 2px solid #172019;
          border-radius: 8px;
          padding: 32px;
          box-shadow: 6px 6px 0 #172019;
        }
        .comp-card.traditional {
          background: #faf2f2;
        }
        .comp-card.civitas {
          background: #f4f8f5;
        }
        .comp-card-header {
          margin-bottom: 20px;
          padding-bottom: 16px;
          border-bottom: 1px solid #172019;
        }
        .comp-badge {
          font-size: 0.62rem;
          font-weight: 900;
          letter-spacing: 0.1em;
          padding: 3px 8px;
          border-radius: 3px;
          display: inline-block;
          margin-bottom: 8px;
        }
        .comp-badge.bad {
          background: #f87171;
          color: #450a0a;
        }
        .comp-badge.good {
          background: #0f5f4f;
          color: #ffffff;
        }
        .comp-card h3 {
          font-size: 1.4rem;
          font-family: Georgia, serif;
          margin: 0;
          color: #172019;
        }
        .comp-list {
          margin: 0;
          padding: 0;
          list-style: none;
          display: flex;
          flex-direction: column;
          gap: 14px;
        }
        .comp-list li {
          font-size: 0.88rem;
          color: #172019;
          line-height: 1.5;
          display: flex;
          align-items: flex-start;
          gap: 10px;
        }
        .icon-cross {
          color: #dc2626;
          font-weight: 900;
          font-size: 0.85rem;
        }
        @media (max-width: 900px) {
          .metrics-container {
            grid-template-columns: 1fr 1fr;
            gap: 20px;
          }
          .comparison-grid {
            grid-template-columns: 1fr;
          }
        }
        @media (max-width: 600px) {
          .metrics-container {
            grid-template-columns: 1fr;
          }
        }
      `}</style>
    </>
  );
}
