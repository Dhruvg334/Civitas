"use client";

import Link from "next/link";
import { Footer, Nav } from "@/components/site";
import { LandingExplorer } from "@/components/landing-explorer";
import { LiveEvidenceSandbox } from "@/components/live-evidence-sandbox";
import { ResolutionSlider } from "@/components/resolution-slider";

function CityLandscapeLeft() {
  return (
    <div className="city-backdrop-wing left-wing" aria-hidden="true">
      <svg viewBox="0 0 420 540" fill="none" xmlns="http://www.w3.org/2000/svg" className="city-svg">
        {/* BACKGROUND BUILDINGS SILHOUETTES */}
        <path d="M40 220 H110 V540 H40 Z" fill="#e8e4d8" opacity="0.6" />
        <path d="M120 160 H190 V540 H120 Z" fill="#d8d4c6" opacity="0.7" />
        <path d="M195 240 H260 V540 H195 Z" fill="#e8e4d8" opacity="0.6" />
        <path d="M270 190 H330 V540 H270 Z" fill="#d2cebf" opacity="0.6" />

        {/* MIDGROUND MUNICIPAL TOWERS & WATER TANK */}
        <rect x="70" y="270" width="75" height="270" fill="#ffffff" stroke="#172019" strokeWidth="2" />
        {/* Tower Windows Grid */}
        {[290, 320, 350, 380, 410, 440, 470, 500].map((y) => (
          <g key={`w-l1-${y}`}>
            <rect x="82" y={y} width="12" height="16" fill="#fef08a" stroke="#172019" strokeWidth="1" />
            <rect x="102" y={y} width="12" height="16" fill="#dce8dd" stroke="#172019" strokeWidth="1" />
            <rect x="122" y={y} width="12" height="16" fill="#fef08a" stroke="#172019" strokeWidth="1" />
          </g>
        ))}
        {/* Antenna Mast with Pulsing Beacon */}
        <line x1="107" y1="270" x2="107" y2="210" stroke="#172019" strokeWidth="2" />
        <circle cx="107" cy="210" r="4" fill="#e84d7a" className="beacon-pulse" />

        {/* MUNICIPAL WATER RESERVOIR TOWER */}
        <ellipse cx="230" cy="300" rx="36" ry="18" fill="#dce8dd" stroke="#172019" strokeWidth="2" />
        <path d="M194 300 V330 C194 340 266 340 266 330 V300 Z" fill="#dce8dd" stroke="#172019" strokeWidth="2" />
        <line x1="206" y1="335" x2="206" y2="540" stroke="#172019" strokeWidth="3" />
        <line x1="254" y1="335" x2="254" y2="540" stroke="#172019" strokeWidth="3" />
        <line x1="230" y1="335" x2="230" y2="540" stroke="#0f5f4f" strokeWidth="4" strokeDasharray="6,4" />
        <line x1="206" y1="380" x2="254" y2="380" stroke="#172019" strokeWidth="2" />
        <line x1="206" y1="440" x2="254" y2="440" stroke="#172019" strokeWidth="2" />
        <line x1="206" y1="500" x2="254" y2="500" stroke="#172019" strokeWidth="2" />
        <text x="230" y="322" fill="#0f5f4f" fontSize="8" fontWeight="bold" textAnchor="middle" letterSpacing="0.08em">BMC WATER</text>

        {/* BRIDGE / FLYOVER ARCH */}
        <path d="M10 460 Q 180 430 360 480" stroke="#172019" strokeWidth="6" fill="none" />
        <path d="M10 468 Q 180 438 360 488" stroke="#0f5f4f" strokeWidth="2" fill="none" />
        {/* Bridge Pillars */}
        <rect x="80" y="456" width="10" height="84" fill="#172019" />
        <rect x="180" y="445" width="10" height="95" fill="#172019" />
        <rect x="280" y="465" width="10" height="75" fill="#172019" />

        {/* SMART STREETLIGHT & TELEMETRY */}
        <path d="M320 540 V360 Q 320 340 345 340" stroke="#172019" strokeWidth="3" fill="none" />
        <circle cx="345" cy="340" r="5" fill="#e3b950" />
        <path d="M338 345 L320 440 L370 440 Z" fill="#e3b950" opacity="0.12" />

        {/* FOREGROUND TREES */}
        <circle cx="45" cy="500" r="22" fill="#0f5f4f" opacity="0.85" />
        <circle cx="65" cy="510" r="18" fill="#172019" opacity="0.85" />
        <rect x="42" y="520" width="6" height="20" fill="#172019" />
        <rect x="63" y="526" width="5" height="14" fill="#172019" />

        {/* GEOLOCATION CALLOUT PIN */}
        <g transform="translate(140, 390)">
          <rect x="0" y="0" width="100" height="24" rx="4" fill="#172019" />
          <circle cx="12" cy="12" r="4" fill="#10b981" className="beacon-pulse" />
          <text x="24" y="15" fill="#ffffff" fontSize="8" fontWeight="bold">20.2961°N · W12</text>
          <path d="M50 24 L50 38" stroke="#172019" strokeWidth="2" strokeDasharray="2,2" />
        </g>
      </svg>
    </div>
  );
}

function CityLandscapeRight() {
  return (
    <div className="city-backdrop-wing right-wing" aria-hidden="true">
      <svg viewBox="0 0 420 540" fill="none" xmlns="http://www.w3.org/2000/svg" className="city-svg">
        {/* BACKGROUND BUILDINGS SILHOUETTES */}
        <path d="M320 200 H390 V540 H320 Z" fill="#e8e4d8" opacity="0.6" />
        <path d="M240 150 H310 V540 H240 Z" fill="#d8d4c6" opacity="0.7" />
        <path d="M170 230 H235 V540 H170 Z" fill="#e8e4d8" opacity="0.6" />
        <path d="M90 180 H160 V540 H90 Z" fill="#d2cebf" opacity="0.6" />

        {/* CONSTRUCTION CRANE */}
        <line x1="280" y1="150" x2="280" y2="70" stroke="#e84d7a" strokeWidth="2" />
        <line x1="230" y1="80" x2="350" y2="80" stroke="#e84d7a" strokeWidth="2" />
        <line x1="280" y1="70" x2="340" y2="80" stroke="#e84d7a" strokeWidth="1.5" />
        <line x1="280" y1="70" x2="240" y2="80" stroke="#e84d7a" strokeWidth="1.5" />
        <line x1="330" y1="80" x2="330" y2="120" stroke="#172019" strokeWidth="1" strokeDasharray="3,2" />
        <rect x="326" y="120" width="8" height="8" fill="#e84d7a" />

        {/* MUNICIPAL HOSPITAL & ADMINISTRATIVE HQ */}
        <rect x="260" y="240" width="90" height="300" fill="#ffffff" stroke="#172019" strokeWidth="2" />
        {/* Hospital Medical Cross */}
        <rect x="298" y="254" width="14" height="4" fill="#e84d7a" />
        <rect x="303" y="249" width="4" height="14" fill="#e84d7a" />
        {/* Windows Grid */}
        {[280, 310, 340, 370, 400, 430, 460, 490].map((y) => (
          <g key={`w-r1-${y}`}>
            <rect x="272" y={y} width="14" height="16" fill="#dce8dd" stroke="#172019" strokeWidth="1" />
            <rect x="298" y={y} width="14" height="16" fill="#fef08a" stroke="#172019" strokeWidth="1" />
            <rect x="324" y={y} width="14" height="16" fill="#dce8dd" stroke="#172019" strokeWidth="1" />
          </g>
        ))}

        {/* CIVIC ACADEMY / SCHOOL FACADE */}
        <polygon points="120,340 210,340 165,300" fill="#ffffff" stroke="#172019" strokeWidth="2" />
        <rect x="125" y="340" width="80" height="200" fill="#fbf9f4" stroke="#172019" strokeWidth="2" />
        {/* Classical Columns */}
        <rect x="135" y="345" width="8" height="195" fill="#ffffff" stroke="#172019" strokeWidth="1.5" />
        <rect x="155" y="345" width="8" height="195" fill="#ffffff" stroke="#172019" strokeWidth="1.5" />
        <rect x="175" y="345" width="8" height="195" fill="#ffffff" stroke="#172019" strokeWidth="1.5" />
        <rect x="195" y="345" width="8" height="195" fill="#ffffff" stroke="#172019" strokeWidth="1.5" />
        <text x="165" y="335" fill="#172019" fontSize="6.5" fontWeight="bold" textAnchor="middle">DAV SCHOOL</text>

        {/* ELECTRICAL TRANSMISSION TOWER */}
        <path d="M50 540 L80 320 L110 540" stroke="#172019" strokeWidth="2" fill="none" />
        <line x1="60" y1="460" x2="100" y2="460" stroke="#172019" strokeWidth="1.5" />
        <line x1="68" y1="390" x2="92" y2="390" stroke="#172019" strokeWidth="1.5" />
        <line x1="50" y1="460" x2="100" y2="390" stroke="#172019" strokeWidth="1" />
        <line x1="110" y1="460" x2="60" y2="390" stroke="#172019" strokeWidth="1" />
        <circle cx="80" cy="320" r="3" fill="#e84d7a" className="beacon-pulse" />

        {/* POSTGIS 500M BUFFER PIN CALLOUT */}
        <g transform="translate(170, 410)">
          <rect x="0" y="0" width="112" height="24" rx="4" fill="#0f5f4f" />
          <circle cx="12" cy="12" r="4" fill="#ffffff" className="beacon-pulse" />
          <text x="24" y="15" fill="#ffffff" fontSize="8" fontWeight="bold">85.8245°E · POSTGIS</text>
          <path d="M56 24 L56 36" stroke="#0f5f4f" strokeWidth="2" strokeDasharray="2,2" />
        </g>

        {/* FOREGROUND TREES */}
        <circle cx="360" cy="510" r="22" fill="#0f5f4f" opacity="0.85" />
        <circle cx="380" cy="520" r="16" fill="#172019" opacity="0.85" />
        <rect x="357" y="525" width="6" height="15" fill="#172019" />
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
                  <span>Citizen opinion treated as ground truth (&quot;it is a pothole&quot; when it is a water burst).</span>
                </li>
                <li>
                  <span className="icon-cross">✕</span>
                  <span>LLM produces ungrounded delivery promises (&quot;fixed in 2 hours&quot;) causing resident anger.</span>
                </li>
                <li>
                  <span className="icon-cross">✕</span>
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
                  <span className="icon-check">✓</span>
                  <span><b>PostGIS 3.4 Clustering:</b> Merges 50 duplicate reports into 1 consolidated incident dossier.</span>
                </li>
                <li>
                  <span className="icon-check">✓</span>
                  <span><b>Evidence Separation:</b> Verifiable media strictly separated from citizen assertions.</span>
                </li>
                <li>
                  <span className="icon-check">✓</span>
                  <span><b>Strict Policy Grounding:</b> Work orders grounded in verified municipal playbooks (e.g. PLAY-WATER-01).</span>
                </li>
                <li>
                  <span className="icon-check">✓</span>
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
          padding: 60px 20px;
          border-bottom: 2px solid #172019;
          background: #fbf9f4;
          text-align: center;
          overflow: hidden;
        }
        .city-backdrop-wing {
          position: absolute;
          top: 0;
          bottom: 0;
          width: 320px;
          pointer-events: none;
          display: flex;
          align-items: flex-end;
          z-index: 1;
          opacity: 0.85;
          transition: opacity 0.3s ease;
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
          max-height: 100%;
        }
        .beacon-pulse {
          animation: beaconBlink 2s infinite ease-in-out;
        }
        @keyframes beaconBlink {
          0%, 100% {
            opacity: 0.4;
            transform: scale(0.9);
          }
          50% {
            opacity: 1;
            transform: scale(1.2);
          }
        }
        .hero-content-center {
          position: relative;
          z-index: 2;
          width: min(calc(100% - 40px), 860px);
          margin: 0 auto;
          display: flex;
          flex-direction: column;
          align-items: center;
        }
        .hero-kicker-pill {
          display: inline-flex;
          align-items: center;
          gap: 8px;
          padding: 4px 12px;
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
        @media (max-width: 1100px) {
          .city-backdrop-wing {
            width: 220px;
            opacity: 0.45;
          }
        }
        @media (max-width: 800px) {
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
