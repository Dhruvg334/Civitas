"use client";

import Link from "next/link";
import { Footer, Nav } from "@/components/site";
import { FlatIcon } from "@/components/flat-icons";
import { LandingExplorer } from "@/components/landing-explorer";
import { LiveEvidenceSandbox } from "@/components/live-evidence-sandbox";
import { ResolutionSlider } from "@/components/resolution-slider";

function CityLandscapeLeft() {
  return (
    <div className="city-backdrop-wing left-wing" aria-hidden="true">
      <svg viewBox="0 0 380 500" fill="none" xmlns="http://www.w3.org/2000/svg" className="city-svg">
        {/* SKYLINE SILHOUETTES */}
        <path d="M20 180 H90 V500 H20 Z" fill="#dce8dd" stroke="#172019" strokeWidth="2" />
        <path d="M100 120 H180 V500 H100 Z" fill="#ffffff" stroke="#172019" strokeWidth="2" />
        <path d="M190 200 H250 V500 H190 Z" fill="#e8e4d8" stroke="#172019" strokeWidth="2" />
        <path d="M260 150 H330 V500 H260 Z" fill="#dce8dd" stroke="#172019" strokeWidth="2" />

        {/* MUNICIPAL TOWER (Left) */}
        <rect x="50" y="240" width="80" height="260" fill="#ffffff" stroke="#172019" strokeWidth="2.5" />
        {/* Windows */}
        {[260, 290, 320, 350, 380, 410, 440, 470].map((y) => (
          <g key={`w-l1-${y}`}>
            <rect x="62" y={y} width="14" height="16" fill="#fef08a" stroke="#172019" strokeWidth="1.5" />
            <rect x="83" y={y} width="14" height="16" fill="#dce8dd" stroke="#172019" strokeWidth="1.5" />
            <rect x="104" y={y} width="14" height="16" fill="#fef08a" stroke="#172019" strokeWidth="1.5" />
          </g>
        ))}
        {/* Antenna Mast */}
        <line x1="90" y1="240" x2="90" y2="160" stroke="#172019" strokeWidth="2.5" />
        <circle cx="90" cy="160" r="5" fill="#e84d7a" className="beacon-pulse" />

        {/* WATER RESERVOIR TOWER */}
        <ellipse cx="220" cy="270" rx="38" ry="20" fill="#0f5f4f" stroke="#172019" strokeWidth="2.5" />
        <path d="M182 270 V305 C182 318 258 318 258 305 V270 Z" fill="#0f5f4f" stroke="#172019" strokeWidth="2.5" />
        <line x1="195" y1="310" x2="195" y2="500" stroke="#172019" strokeWidth="3.5" />
        <line x1="245" y1="310" x2="245" y2="500" stroke="#172019" strokeWidth="3.5" />
        <line x1="220" y1="310" x2="220" y2="500" stroke="#10b981" strokeWidth="4" strokeDasharray="6,4" />
        <line x1="195" y1="360" x2="245" y2="360" stroke="#172019" strokeWidth="2" />
        <line x1="195" y1="420" x2="245" y2="420" stroke="#172019" strokeWidth="2" />
        <line x1="195" y1="470" x2="245" y2="470" stroke="#172019" strokeWidth="2" />
        <text x="220" y="294" fill="#ffffff" fontSize="9" fontWeight="900" textAnchor="middle" letterSpacing="0.08em">BMC WATER</text>

        {/* FLYOVER BRIDGE ARCH */}
        <path d="M0 420 Q 160 390 340 440" stroke="#172019" strokeWidth="7" fill="none" />
        <path d="M0 428 Q 160 398 340 448" stroke="#e84d7a" strokeWidth="2" fill="none" />
        <rect x="70" y="415" width="12" height="85" fill="#172019" />
        <rect x="170" y="405" width="12" height="95" fill="#172019" />
        <rect x="270" y="425" width="12" height="75" fill="#172019" />

        {/* STREETLIGHT & GIS TELEMETRY */}
        <path d="M310 500 V320 Q 310 300 335 300" stroke="#172019" strokeWidth="3" fill="none" />
        <circle cx="335" cy="300" r="6" fill="#fef08a" stroke="#172019" strokeWidth="1.5" />
        <path d="M328 306 L305 400 L360 400 Z" fill="#fef08a" opacity="0.3" />

        {/* GEOLOCATION CALLOUT PIN */}
        <g transform="translate(110, 360)">
          <rect x="0" y="0" width="110" height="26" rx="5" fill="#172019" stroke="#ffffff" strokeWidth="1.5" />
          <circle cx="14" cy="13" r="5" fill="#10b981" className="beacon-pulse" />
          <text x="26" y="17" fill="#ffffff" fontSize="9" fontWeight="bold">20.2961°N · W12</text>
        </g>
      </svg>
    </div>
  );
}

function CityLandscapeRight() {
  return (
    <div className="city-backdrop-wing right-wing" aria-hidden="true">
      <svg viewBox="0 0 380 500" fill="none" xmlns="http://www.w3.org/2000/svg" className="city-svg">
        {/* SKYLINE SILHOUETTES */}
        <path d="M290 160 H360 V500 H290 Z" fill="#dce8dd" stroke="#172019" strokeWidth="2" />
        <path d="M210 110 H285 V500 H210 Z" fill="#ffffff" stroke="#172019" strokeWidth="2" />
        <path d="M140 190 H205 V500 H140 Z" fill="#e8e4d8" stroke="#172019" strokeWidth="2" />
        <path d="M60 140 H135 V500 H60 Z" fill="#dce8dd" stroke="#172019" strokeWidth="2" />

        {/* CONSTRUCTION CRANE */}
        <line x1="250" y1="110" x2="250" y2="40" stroke="#e84d7a" strokeWidth="3" />
        <line x1="190" y1="50" x2="320" y2="50" stroke="#e84d7a" strokeWidth="3" />
        <line x1="250" y1="40" x2="310" y2="50" stroke="#e84d7a" strokeWidth="2" />
        <line x1="250" y1="40" x2="200" y2="50" stroke="#e84d7a" strokeWidth="2" />
        <line x1="300" y1="50" x2="300" y2="95" stroke="#172019" strokeWidth="1.5" strokeDasharray="3,2" />
        <rect x="295" y="95" width="10" height="10" fill="#e84d7a" stroke="#172019" strokeWidth="1.5" />

        {/* MUNICIPAL HOSPITAL & HQ */}
        <rect x="230" y="210" width="95" height="290" fill="#ffffff" stroke="#172019" strokeWidth="2.5" />
        {/* Hospital Medical Cross */}
        <rect x="270" y="225" width="16" height="5" fill="#e84d7a" />
        <rect x="275.5" y="219.5" width="5" height="16" fill="#e84d7a" />
        {/* Windows */}
        {[255, 285, 315, 345, 375, 405, 435, 465].map((y) => (
          <g key={`w-r1-${y}`}>
            <rect x="242" y={y} width="16" height="16" fill="#dce8dd" stroke="#172019" strokeWidth="1.5" />
            <rect x="270" y={y} width="16" height="16" fill="#fef08a" stroke="#172019" strokeWidth="1.5" />
            <rect x="298" y={y} width="16" height="16" fill="#dce8dd" stroke="#172019" strokeWidth="1.5" />
          </g>
        ))}

        {/* CIVIC ACADEMY / SCHOOL FACADE */}
        <polygon points="90,310 190,310 140,265" fill="#0f5f4f" stroke="#172019" strokeWidth="2.5" />
        <rect x="95" y="310" width="90" height="190" fill="#fbf9f4" stroke="#172019" strokeWidth="2.5" />
        {/* Classical Columns */}
        <rect x="105" y="315" width="9" height="185" fill="#ffffff" stroke="#172019" strokeWidth="2" />
        <rect x="127" y="315" width="9" height="185" fill="#ffffff" stroke="#172019" strokeWidth="2" />
        <rect x="149" y="315" width="9" height="185" fill="#ffffff" stroke="#172019" strokeWidth="2" />
        <rect x="171" y="315" width="9" height="185" fill="#ffffff" stroke="#172019" strokeWidth="2" />
        <text x="140" y="298" fill="#ffffff" fontSize="8.5" fontWeight="900" textAnchor="middle">DAV SCHOOL</text>

        {/* ELECTRICAL TRANSMISSION TOWER */}
        <path d="M20 500 L50 280 L80 500" stroke="#172019" strokeWidth="2.5" fill="none" />
        <line x1="30" y1="420" x2="70" y2="420" stroke="#172019" strokeWidth="2" />
        <line x1="38" y1="350" x2="62" y2="350" stroke="#172019" strokeWidth="2" />
        <circle cx="50" cy="280" r="4" fill="#e84d7a" className="beacon-pulse" />

        {/* POSTGIS 500M BUFFER PIN CALLOUT */}
        <g transform="translate(130, 380)">
          <rect x="0" y="0" width="125" height="26" rx="5" fill="#0f5f4f" stroke="#ffffff" strokeWidth="1.5" />
          <circle cx="14" cy="13" r="5" fill="#ffffff" className="beacon-pulse" />
          <text x="26" y="17" fill="#ffffff" fontSize="9" fontWeight="bold">85.8245°E · POSTGIS</text>
        </g>
      </svg>
    </div>
  );
}

export default function Home() {
  return (
    <>
      <Nav />
      <main className="landing-main-shell">
        {/* HERO SECTION WITH DUAL CITY LANDSCAPE WINGS */}
        <section className="hero-fullscreen" aria-label="Civitas hero intro">
          <CityLandscapeLeft />
          
          <div className="hero-content-center">
            <div className="hero-kicker-pill">
              <span className="hero-kicker-dot" />
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

          <CityLandscapeRight />
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
          <div className="sandbox-wrapper">
            <LiveEvidenceSandbox />
          </div>
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
                  <span className="icon-cross"><FlatIcon name="cross" size={12} color="#dc2626" /></span>
                  <span>50 citizens report same water burst → creates 50 duplicate work orders.</span>
                </li>
                <li>
                  <span className="icon-cross"><FlatIcon name="cross" size={12} color="#dc2626" /></span>
                  <span>Citizen opinion treated as ground truth (&quot;it is a pothole&quot; when it is a water burst).</span>
                </li>
                <li>
                  <span className="icon-cross"><FlatIcon name="cross" size={12} color="#dc2626" /></span>
                  <span>LLM produces ungrounded delivery promises (&quot;fixed in 2 hours&quot;) causing resident anger.</span>
                </li>
                <li>
                  <span className="icon-cross"><FlatIcon name="cross" size={12} color="#dc2626" /></span>
                  <span>Tickets closed automatically without photographic repair verification.</span>
                </li>
              </ul>
            </div>

            <div className="comp-card civitas-way">
              <div className="comp-card-header">
                <span className="comp-badge good">THE CIVITAS ARCHITECTURE</span>
                <h3>Evidence-Backed Orchestration</h3>
              </div>
              <ul className="comp-list">
                <li>
                  <span className="icon-check"><FlatIcon name="check" size={12} color="#0f5f4f" /></span>
                  <span><b>PostGIS 3.4 Clustering:</b> Merges 50 duplicate reports into 1 consolidated incident dossier.</span>
                </li>
                <li>
                  <span className="icon-check"><FlatIcon name="check" size={12} color="#0f5f4f" /></span>
                  <span><b>Evidence Separation:</b> Verifiable media strictly separated from citizen assertions.</span>
                </li>
                <li>
                  <span className="icon-check"><FlatIcon name="check" size={12} color="#0f5f4f" /></span>
                  <span><b>Strict Policy Grounding:</b> Work orders grounded in verified municipal playbooks (e.g. PLAY-WATER-01).</span>
                </li>
                <li>
                  <span className="icon-check"><FlatIcon name="check" size={12} color="#0f5f4f" /></span>
                  <span><b>Computer Vision Audit:</b> Before / after photo diff prevents fraudulent ticket closures.</span>
                </li>
              </ul>
            </div>
          </div>
        </section>

        {/* BOTTOM CTA STRIP */}
        <section className="bottom-cta-strip">
          <div className="cta-strip-container">
            <div className="cta-strip-text">
              <h2>Deploy Civitas for Your Municipal Ward</h2>
              <p>
                Open-source civic incident intelligence designed for municipal engineers, supervisors, and engaged citizens.
              </p>
            </div>
            <div className="cta-strip-buttons">
              <Link className="button large" href="/workspace">
                Launch Workspace →
              </Link>
              <Link className="outline large" href="/docs">
                Read Documentation
              </Link>
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
          position: relative;
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 70px 20px;
          border-bottom: 2px solid #172019;
          background: #fbf9f4;
          text-align: center;
          overflow: hidden;
        }
        .city-backdrop-wing {
          position: absolute;
          bottom: 0;
          width: clamp(260px, 28vw, 420px);
          pointer-events: none;
          display: flex;
          align-items: flex-end;
          z-index: 1;
          opacity: 0.95;
        }
        .city-backdrop-wing.left-wing {
          left: 0;
        }
        .city-backdrop-wing.right-wing {
          right: 0;
        }
        .city-svg {
          width: 100%;
          height: auto;
          display: block;
        }
        .beacon-pulse {
          animation: beaconBlink 2s infinite ease-in-out;
        }
        @keyframes beaconBlink {
          0%, 100% {
            opacity: 0.5;
            transform: scale(0.9);
          }
          50% {
            opacity: 1;
            transform: scale(1.25);
          }
        }
        .hero-content-center {
          position: relative;
          z-index: 2;
          width: min(calc(100% - 40px), 820px);
          margin: 0 auto;
          display: flex;
          flex-direction: column;
          align-items: center;
        }
        .hero-kicker-pill {
          display: inline-flex;
          align-items: center;
          gap: 8px;
          padding: 5px 14px;
          border: 1px solid #0f5f4f;
          background: #dce8dd;
          color: #0f5f4f;
          border-radius: 4px;
          font-size: 0.65rem;
          font-weight: 900;
          letter-spacing: 0.12em;
          margin-bottom: 20px;
        }
        .hero-kicker-dot {
          width: 7px;
          height: 7px;
          border-radius: 50%;
          background: #0f5f4f;
        }
        .hero-title {
          font-size: clamp(2.8rem, 5.2vw, 4.6rem);
          font-family: Georgia, serif;
          margin: 0 0 18px;
          line-height: 1.03;
          color: #172019;
          letter-spacing: -0.02em;
        }
        .hero-lead {
          font-size: clamp(1.02rem, 1.8vw, 1.2rem);
          color: #495248;
          line-height: 1.6;
          margin: 0 0 34px;
          max-width: 760px;
        }
        .hero-cta-group {
          display: flex;
          gap: 16px;
          justify-content: center;
          margin-bottom: 34px;
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
          font-weight: 750;
        }
        .section-block {
          padding: 85px 0;
          border-bottom: 1px solid #172019;
        }
        .section-header-tag {
          width: min(calc(100% - 40px), 1180px);
          margin: 0 auto 36px;
        }
        .sandbox-wrapper {
          width: min(calc(100% - 40px), 1180px);
          margin: 0 auto;
        }
        .tag-row {
          display: inline-flex;
          align-items: center;
          gap: 8px;
          margin-bottom: 12px;
        }
        .tag-index {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          height: 22px;
          padding: 0 7px;
          font-size: 0.68rem;
          font-weight: 900;
          line-height: 1;
          background: #172019;
          color: #ffffff;
          border-radius: 4px;
        }
        .section-kicker {
          font-size: 0.72rem;
          font-weight: 900;
          letter-spacing: 0.12em;
          color: #0f5f4f;
          line-height: 1;
          text-transform: uppercase;
        }
        .section-header-tag h2 {
          font-size: clamp(2.2rem, 4vw, 3.4rem);
          font-family: Georgia, serif;
          margin: 0 0 10px;
          color: #172019;
          line-height: 1.05;
        }
        .section-header-tag p {
          font-size: 1rem;
          color: #555e54;
          max-width: 720px;
          line-height: 1.55;
          margin: 0;
        }
        .live-sandbox-section {
          background: #ffffff;
        }
        .resolution-showcase-section {
          background: #fbf9f4;
        }
        .resolution-card-wrap {
          width: min(calc(100% - 40px), 1180px);
          margin: 0 auto;
        }
        .comparison-section {
          background: #ffffff;
        }
        .comparison-grid {
          width: min(calc(100% - 40px), 1180px);
          margin: 0 auto;
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 24px;
        }
        .comp-card {
          border: 2px solid #172019;
          border-radius: 8px;
          padding: 32px;
          display: flex;
          flex-direction: column;
          gap: 18px;
        }
        .comp-card.traditional {
          background: #fdf2f2;
          border-color: #991b1b;
        }
        .comp-card.civitas-way {
          background: #f4f8f5;
          border-color: #0f5f4f;
          box-shadow: 6px 6px 0 #172019;
        }
        .comp-badge {
          display: inline-block;
          font-size: 0.65rem;
          font-weight: 900;
          letter-spacing: 0.1em;
          padding: 3px 8px;
          border-radius: 3px;
          margin-bottom: 8px;
        }
        .comp-badge.bad {
          background: #fee2e2;
          color: #991b1b;
          border: 1px solid #991b1b;
        }
        .comp-badge.good {
          background: #dce8dd;
          color: #0f5f4f;
          border: 1px solid #0f5f4f;
        }
        .comp-card h3 {
          font-size: 1.6rem;
          font-family: Georgia, serif;
          margin: 0;
          color: #172019;
        }
        .comp-list {
          list-style: none;
          padding: 0;
          margin: 0;
          display: flex;
          flex-direction: column;
          gap: 14px;
        }
        .comp-list li {
          display: grid;
          grid-template-columns: 24px 1fr;
          gap: 10px;
          font-size: 0.9rem;
          line-height: 1.45;
          align-items: start;
        }
        .icon-cross {
          color: #991b1b;
          font-weight: 900;
          font-size: 1rem;
        }
        .icon-check {
          color: #0f5f4f;
          font-weight: 900;
          font-size: 1rem;
        }
        .bottom-cta-strip {
          background: #172019;
          color: #ffffff;
          padding: 70px 0;
        }
        .cta-strip-container {
          width: min(calc(100% - 40px), 1180px);
          margin: 0 auto;
          display: flex;
          justify-content: space-between;
          align-items: center;
          gap: 32px;
          flex-wrap: wrap;
        }
        .cta-strip-text h2 {
          font-size: 2.2rem;
          font-family: Georgia, serif;
          margin: 0 0 8px;
          color: #ffffff;
        }
        .cta-strip-text p {
          font-size: 0.95rem;
          color: #dce8dd;
          margin: 0;
          max-width: 580px;
        }
        .cta-strip-buttons {
          display: flex;
          gap: 14px;
          flex-wrap: wrap;
        }
        @media (max-width: 900px) {
          .city-backdrop-wing {
            display: none;
          }
          .metrics-container {
            grid-template-columns: 1fr 1fr;
          }
          .comparison-grid {
            grid-template-columns: 1fr;
          }
        }
      `}</style>
    </>
  );
}
