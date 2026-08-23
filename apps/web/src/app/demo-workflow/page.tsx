"use client";

import { useState } from "react";
import { Footer, Nav, Status } from "@/components/site";
import { FlatIcon } from "@/components/flat-icons";
import { AgentTraceVisualizer } from "@/components/agent-trace-visualizer";

const stages = [
  {
    id: "intake",
    label: "Multimodal Intake",
    title: "Omnichannel reports enter with zero-trust EXIF & privacy extraction.",
    summary:
      "Reports arrive via WhatsApp, Telegram, Open311 GeoReport v2, or Web. Zero-trust extraction strips device serials, extracts GPS/timestamps, and accepts voice notes without data loss.",
    output: "3 omnichannel streams ingested",
    facts: [
      "CHANNEL · WhatsApp Webhook (Location dropped + Photo attached)",
      "CHANNEL · Telegram Bot (Citizen text: 'Bikes slipping by gate')",
      "SECURITY · EXIF GPS parsed (20.29614, 85.82451), camera tracking stripped",
    ],
  },
  {
    id: "geospatial_vision",
    label: "Geo & Vision Triage",
    title: "H3 hexagonal indexing and geometric defect sizing classify the site.",
    summary:
      "Reports map to discrete global H3 hex cells (Res 8/9). Historical recurrence flags CHRONIC_FAILURE_ZONE hotspots, vision models compute defect area (cm²) & depth (mm), and SCADA IoT telemetry detects water pressure drops.",
    output: "H3: 8860b29849fffff (Chronic Failure Zone)",
    facts: [
      "H3 CELL · 8860b29849fffff (5 incidents in 6mo → CHRONIC_FAILURE_ZONE)",
      "DEFECT METRIC · 2,400 cm² surface area, 65mm cavity depth (PCI deduction: 48)",
      "SCADA TELEMETRY · Distribution zone valve PRV-12 pressure drop: -1.8 bar",
    ],
  },
  {
    id: "grounding_guardrails",
    label: "Knowledge & Guardrails",
    title: "Hybrid multi-vector retrieval with reciprocal rank fusion & guardrails.",
    summary:
      "BM25 sparse keyword matching combines with dense semantic vectors via RRF (k=60). Statutory jurisdiction resolves to Municipal Water Supply (preventing highway ping-pong) and guardrails verify SLA targets.",
    output: "RRF Score: 0.032 · Guardrail: PASS",
    facts: [
      "HYBRID RRF · PLAY-WATER-01 (Municipal Main Line Rupture SOP)",
      "JURISDICTION · Municipal Corporation Ward 12 (Statutory SLA: 24h)",
      "GUARDRAIL · Validated department against catalog; prompt injection filter clean",
    ],
  },
  {
    id: "priority_boq",
    label: "Priority & BOQ Costing",
    title: "Vulnerability exposure accelerates SLA; BOQ calculates Schedule of Rates.",
    summary:
      "Proximity to DAV Public School gate (14m) dynamically escalates priority to P1 Critical and compresses statutory SLA from 24h to 4h. The automated BOQ generator estimates repair materials in INR and USD.",
    output: "P1 CRITICAL · SLA: 4h · BOQ: ₹28,450",
    facts: [
      "VULNERABILITY · School buffer (≤100m) → +25 priority pts, 0.5x SLA multiplier",
      "DYNAMIC SLA · Accelerated from 24h to 4h emergency dispatch envelope",
      "MUNICIPAL BOQ · Dense Bituminous Macadam (0.45t) + Ductile Sleeve + Labor = ₹28,450 ($328.9 USD)",
    ],
  },
  {
    id: "resolution_fraud",
    label: "Resolution & Anti-Fraud",
    title: "64-bit dHash perceptual verification and cryptographic SHA-256 certification.",
    summary:
      "Contractor closure photos undergo perceptual difference hashing (dHash) to prevent recycled photo fraud. Resolution verification classifies outcome as RESOLVED, opening the 72-hour citizen dispute window.",
    output: "dHash Distance: 28/64 · SHA-256 SEALED",
    facts: [
      "ANTI-FRAUD · dHash Hamming distance 28/64 (Passes identical photo check)",
      "72H DISPUTE · Citizen review window active with one-click rebuttal re-open",
      "AUDIT CERTIFICATE · Sealed with SHA-256 digest: e9f4a8c17b5e...9d82ae",
    ],
  },
  {
    id: "open_data",
    label: "Public Trust & Open Data",
    title: "Differential privacy spatial jitter, GeoJSON feeds, and vendor analytics.",
    summary:
      "Automated PII scrubbing redacts citizen phone numbers and addresses. Differential privacy applies bounded ±25m Gaussian spatial perturbation to public RFC 7946 GeoJSON/CSV feeds while contractor scorecards track vendor MTTR.",
    output: "RFC 7946 GeoJSON · Vendor Score: 92.4/100",
    facts: [
      "PRIVACY · PII redacted; ±25m Gaussian spatial jitter applied for open data",
      "OPEN DATA · Live RFC 7946 GeoJSON and tabular CSV public feeds available",
      "VENDOR SCORECARD · Apex Dewatering: 93.5% SLA compliance, 6.4h MTTR (Tier 1 Excellent)",
    ],
  },
];

export default function Demo() {
  const [active, setActive] = useState(0);
  const [showTrace, setShowTrace] = useState(false);
  const stage = stages[active];

  return (
    <>
      <Nav />
      <main className="demo-shell rich-demo">
        <header className="demo-header-banner">
          <div>
            <span className="workspace-kicker">GOLDEN RUNTIME SLICE / BHUBANESWAR DEMO</span>
            <h1>Water near a school is not three separate tickets.</h1>
            <p>
              Follow the seeded water-leak incident through real workflow steps: intake context,
              evidence boundaries, deterministic ML, policy grounding, routing, planning, critic checks,
              and supervisor authorization.
            </p>
          </div>
          <div className="demo-header-actions">
            <Status tone="good">OFFLINE DEMO RUNTIME</Status>
            <button
              onClick={() => setShowTrace(!showTrace)}
              className="outline small-trace-btn"
            >
              {showTrace ? "Hide Agent Trace" : "View Agent Trace (LangGraph)"}
            </button>
          </div>
        </header>

        {showTrace && (
          <section className="trace-drawer">
            <AgentTraceVisualizer
              incidentId="INC-0241"
              workflowId="WF-DEMO-0241"
              currentStep={stage.id}
            />
          </section>
        )}

        {/* PLAYABLE YOUTUBE VIDEO DEMO WINDOW */}
        <section className="demo-video-window-card" aria-label="Official Video Demonstration">
          <div className="video-window-header">
            <div className="window-dots-group">
              <span className="dot dot-red" />
              <span className="dot dot-yellow" />
              <span className="dot dot-green" />
              <span className="window-header-title">CIVITAS SYSTEM ARCHITECTURE & END-TO-END DEMO</span>
            </div>
            <div className="window-header-actions">
              <span className="video-badge">
                <FlatIcon name="sparkles" size={11} color="#0f5f4f" /> OFFICIAL 1080P WALKTHROUGH
              </span>
              <a
                href="https://youtu.be/jqiI4XmeBBs"
                target="_blank"
                rel="noopener noreferrer"
                className="open-yt-link"
                title="Open video on YouTube in new tab"
              >
                <FlatIcon name="explore" size={12} /> Open in YouTube ↗
              </a>
            </div>
          </div>

          <div className="video-iframe-container">
            <iframe
              src="https://www.youtube-nocookie.com/embed/jqiI4XmeBBs?rel=0"
              title="Civitas Autonomous Civic Intelligence & Dispatch Walkthrough"
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
              allowFullScreen
              className="demo-video-iframe"
            />
          </div>

          <div className="video-window-footer">
            <div className="video-meta-block">
              <b>Demonstrated System Capabilities:</b>
              <p>
                Omnichannel WhatsApp / Web intake → PostGIS spatial deduplication → LangGraph critic verification → Policy playbook grounding → Zero-shot photographic repair audit.
              </p>
            </div>
          </div>
        </section>

        <section className="demo-casebar">
          <div>
            <span>INCIDENT ID</span>
            <b>INC-0241 · School crossing water leak</b>
          </div>
          <div>
            <span>INPUT REPORTS</span>
            <b>03 related citizen reports</b>
          </div>
          <div>
            <span>GIS LOCATION</span>
            <b>20.2961 N, 85.8245 E (Ward 12)</b>
          </div>
          <div>
            <span>WORKFLOW STATE</span>
            <Status tone="warn">WAITING_FOR_REVIEW</Status>
          </div>
        </section>

        <div className="demo-grid">
          <aside className="demo-stepper" aria-label="Demo stages">
            {stages.map((item, index) => (
              <button
                onClick={() => setActive(index)}
                className={`step-btn ${active === index ? "active" : active > index ? "passed" : ""}`}
                key={item.id}
              >
                <span className="step-badge-num">{String(index + 1).padStart(2, "0")}</span>
                <div>
                  <b>{item.label}</b>
                  <small style={{ display: "inline-flex", alignItems: "center", gap: "4px" }}>
                    {index < active ? (
                      <>
                        <FlatIcon name="check" size={10} color="#0f5f4f" /> Complete
                      </>
                    ) : index === active ? (
                      "Active Step"
                    ) : (
                      "Queued"
                    )}
                  </small>
                </div>
              </button>
            ))}
          </aside>

          <section className="demo-stage">
            <div className="demo-stage-index">
              <span>{String(active + 1).padStart(2, "0")}</span>
              <p>{stage.label.toUpperCase()} STEP</p>
            </div>
            <h2>{stage.title}</h2>
            <p className="stage-lede">{stage.summary}</p>

            <div className="demo-output">
              <div className="demo-output-header">
                <span>STAGE AGENT OUTPUT</span>
                <Status tone={active === 5 ? "warn" : "good"}>{stage.output}</Status>
              </div>
              <div className="demo-facts">
                {stage.facts.map((fact) => (
                  <article key={fact}>
                    <span className="fact-bullet">•</span>
                    <p>{fact}</p>
                  </article>
                ))}
              </div>
            </div>

            {/* STAGE-SPECIFIC INTERACTIVE CARDS */}
            {active === 0 && (
              <div className="report-evidence-grid">
                <article className="report-card">
                  <span className="card-tag">WHATSAPP WEBHOOK</span>
                  <b>“Water gushing near DAV school gate.”</b>
                  <small>EXIF GPS: 20.29614, 85.82451 · Device tags stripped</small>
                </article>
                <article className="report-card">
                  <span className="card-tag">TELEGRAM BOT</span>
                  <b>“Bikes are slipping by the gate.”</b>
                  <small>Inbound text message · Voice note transcribed</small>
                </article>
                <article className="report-card">
                  <span className="card-tag">OPEN311 GEOMARKER</span>
                  <b>GeoReport v2 Service Request</b>
                  <small>Standardized RFC payload · Zero data truncation</small>
                </article>
              </div>
            )}

            {active === 1 && (
              <div className="signal-board-grid">
                <article className="signal-card">
                  <span className="signal-tag">H3 SPATIAL CLUSTER</span>
                  <b>Cell: 8860b29849fffff</b>
                  <small>5 incidents in 6mo → CHRONIC_FAILURE_ZONE</small>
                </article>
                <article className="signal-card">
                  <span className="signal-tag">GEOMETRIC DEFECT SIZING</span>
                  <b>2,400 cm² · 65mm Depth</b>
                  <small>PCI Deduction: 48 pts (Fair Condition)</small>
                </article>
                <article className="signal-card">
                  <span className="signal-tag">SCADA IOT TRANSDUCER</span>
                  <b>PRV-12: -1.8 bar drop</b>
                  <small>Subsurface distribution anomaly confirmed</small>
                </article>
              </div>
            )}

            {active === 2 && (
              <div className="knowledge-evidence-grid">
                <div className="know-card">
                  <span className="know-tag">HYBRID BM25 + DENSE RRF</span>
                  <b>PLAY-WATER-01 (RRF: 0.032)</b>
                  <p>Municipal main line rupture response procedure retrieved with citation verification.</p>
                </div>
                <div className="know-card">
                  <span className="know-tag">STATUTORY JURISDICTION</span>
                  <b>Municipal Ward 12</b>
                  <p>Resolved to Urban Water Supply (preventing State PWD ping-pong).</p>
                </div>
                <div className="know-card">
                  <span className="know-tag">HALLUCINATION GUARDRAIL</span>
                  <b>Verdict: PASS</b>
                  <p>Verified against official statutory catalog; 0 fabricated token IDs.</p>
                </div>
              </div>
            )}

            {active === 3 && (
              <div className="signal-board-grid">
                <article className="signal-card">
                  <span className="signal-tag">DYNAMIC SLA ACCELERATION</span>
                  <b>4 Hours (was 24h)</b>
                  <small>DAV Public School buffer (14m) triggers emergency SLA</small>
                </article>
                <article className="signal-card">
                  <span className="signal-tag">SCHEDULE OF RATES BOQ</span>
                  <b>₹28,450 ($328.9 USD)</b>
                  <small>DBM hot mix + ductile sleeve + vibratory compactor</small>
                </article>
                <article className="signal-card">
                  <span className="signal-tag">CREW DISPATCH BUNDLE</span>
                  <b>BUNDLE-CREW-001</b>
                  <small>Multi-stop route clustered in H3 hex cell 8860b29849fffff</small>
                </article>
              </div>
            )}

            {active === 4 && (
              <div className="signal-board-grid">
                <article className="signal-card">
                  <span className="signal-tag">PERCEPTUAL ANTI-FRAUD</span>
                  <b>64-bit dHash Distance: 28</b>
                  <small>Verified authentic post-repair photo (not recycled)</small>
                </article>
                <article className="signal-card">
                  <span className="signal-tag">72H CITIZEN DISPUTE</span>
                  <b>Active Countdown</b>
                  <small>One-click rebuttal submission with auto-escalation</small>
                </article>
                <article className="signal-card">
                  <span className="signal-tag">SHA-256 AUDIT SEAL</span>
                  <b>e9f4a8c17b5e...9d82ae</b>
                  <small>Cryptographically sealed immutable municipal certificate</small>
                </article>
              </div>
            )}

            {active === 5 && (
              <div className="review-demo-box">
                <div className="review-info">
                  <span className="review-tag">PUBLIC TRUST & CONTINUOUS ANALYTICS</span>
                  <b>RFC 7946 GeoJSON + Differential Privacy Jitter (±25m)</b>
                  <p>
                    Citizen PII scrubbed. Contractor scorecards track vendor SLA compliance (93.5%), MTTR (6.4h), and dispute rates (2.1%).
                  </p>
                </div>
                <div className="review-actions-row">
                  <button className="button small" onClick={() => window.open("/open-data", "_blank")}>View Open Data Portal</button>
                  <button className="outline small" onClick={() => window.open("/analytics", "_blank")}>View Vendor Analytics</button>
                  <button className="outline small" onClick={() => window.open("/dispatch", "_blank")}>View Crew Dispatch</button>
                </div>
              </div>
            )}

            <footer className="stage-footer-bar">
              <div className="trace-info">
                <span>WORKFLOW TRACE ID:</span>
                <code>trace-demo-water · {stage.id} node</code>
              </div>
              <div className="nav-buttons">
                <button
                  disabled={active === 0}
                  onClick={() => setActive((v) => v - 1)}
                  className="prev-btn"
                >
                  ← Previous Step
                </button>
                <button
                  disabled={active === stages.length - 1}
                  onClick={() => setActive((v) => v + 1)}
                  className="next-btn"
                >
                  Next Step →
                </button>
              </div>
            </footer>
          </section>
        </div>
      </main>
      <Footer />

      <style jsx>{`
        .demo-shell {
          width: min(calc(100% - 40px), 1180px);
          margin: 40px auto 90px;
        }
        .demo-header-banner {
          display: flex;
          justify-content: space-between;
          align-items: flex-end;
          gap: 30px;
          padding-bottom: 28px;
          border-bottom: 2px solid #172019;
        }
        .demo-header-banner h1 {
          font-size: clamp(2.5rem, 4.5vw, 4.2rem);
          line-height: 0.92;
          margin: 8px 0;
          font-family: Georgia, serif;
        }
        .demo-header-banner p {
          max-width: 680px;
          color: #495248;
          font-size: 0.95rem;
          line-height: 1.6;
          margin: 0;
        }
        .demo-header-actions {
          display: flex;
          flex-direction: column;
          align-items: flex-end;
          gap: 12px;
        }
        .small-trace-btn {
          font-size: 0.72rem !important;
          padding: 8px 12px !important;
        }
        .trace-drawer {
          margin: 20px 0;
          border: 1px solid #172019;
          box-shadow: 4px 4px 0 #172019;
        }
        .demo-video-window-card {
          margin: 24px 0;
          border: 2px solid #172019;
          background: #ffffff;
          box-shadow: 6px 6px 0 #172019;
          border-radius: 8px;
          overflow: hidden;
        }
        .video-window-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 10px 16px;
          background: #fbf9f4;
          border-bottom: 2px solid #172019;
          flex-wrap: wrap;
          gap: 8px;
        }
        .window-dots-group {
          display: flex;
          align-items: center;
          gap: 8px;
        }
        .dot {
          width: 10px;
          height: 10px;
          border-radius: 50%;
          border: 1px solid #172019;
          display: inline-block;
        }
        .dot-red { background: #f87171; }
        .dot-yellow { background: #fde047; }
        .dot-green { background: #4ade80; }
        .window-header-title {
          font-size: 0.68rem;
          font-weight: 900;
          letter-spacing: 0.08em;
          color: #172019;
          margin-left: 6px;
        }
        .window-header-actions {
          display: flex;
          align-items: center;
          gap: 12px;
        }
        .video-badge {
          display: inline-flex;
          align-items: center;
          gap: 4px;
          font-size: 0.62rem;
          font-weight: 850;
          color: #0f5f4f;
          background: #dce8dd;
          padding: 3px 8px;
          border-radius: 3px;
          border: 1px solid #0f5f4f;
        }
        .open-yt-link {
          font-size: 0.72rem;
          font-weight: 750;
          color: #172019;
          display: inline-flex;
          align-items: center;
          gap: 4px;
          text-decoration: none;
        }
        .open-yt-link:hover {
          text-decoration: underline;
        }
        .video-iframe-container {
          position: relative;
          width: 100%;
          padding-bottom: 56.25%; /* 16:9 Aspect Ratio */
          height: 0;
          background: #172019;
        }
        .demo-video-iframe {
          position: absolute;
          top: 0;
          left: 0;
          width: 100%;
          height: 100%;
          border: 0;
        }
        .video-window-footer {
          padding: 12px 18px;
          background: #fbf9f4;
          border-top: 1px solid #e2ded4;
        }
        .video-meta-block b {
          font-size: 0.78rem;
          color: #172019;
          display: block;
        }
        .video-meta-block p {
          font-size: 0.74rem;
          color: #555e54;
          margin: 2px 0 0;
          line-height: 1.4;
        }
        .demo-casebar {
          display: grid;
          grid-template-columns: 1.4fr 1fr 1.2fr 1fr;
          margin: 24px 0;
          border: 1px solid #172019;
          background: #ffffff;
          box-shadow: 3px 3px 0 #172019;
        }
        .demo-casebar > div {
          padding: 14px 18px;
          border-right: 1px solid #e2ded4;
          display: flex;
          flex-direction: column;
          gap: 4px;
        }
        .demo-casebar > div:last-child {
          border-right: 0;
        }
        .demo-casebar span {
          font-size: 0.58rem;
          font-weight: 850;
          letter-spacing: 0.1em;
          color: #687067;
        }
        .demo-casebar b {
          font-size: 0.78rem;
          color: #172019;
        }
        .demo-grid {
          display: grid;
          grid-template-columns: 240px minmax(0, 1fr);
          border: 1px solid #172019;
          box-shadow: 4px 4px 0 #172019;
          background: #ffffff;
          min-height: 580px;
        }
        .demo-stepper {
          border-right: 1px solid #172019;
          background: #fbf9f4;
        }
        .step-btn {
          width: 100%;
          border: 0;
          border-bottom: 1px solid #e2ded4;
          background: transparent;
          padding: 16px 18px;
          text-align: left;
          display: grid;
          grid-template-columns: 28px 1fr;
          gap: 10px;
          align-items: center;
          cursor: pointer;
          transition: background 0.15s ease;
        }
        .step-btn:hover,
        .step-btn.active {
          background: #ffffff;
        }
        .step-btn.active {
          box-shadow: inset 4px 0 0 #e84d7a;
        }
        .step-btn.passed .step-badge-num {
          color: #0f5f4f;
        }
        .step-badge-num {
          font-size: 0.7rem;
          font-weight: 900;
          color: #687067;
        }
        .step-btn b {
          display: block;
          font-size: 0.78rem;
          color: #172019;
        }
        .step-btn small {
          display: block;
          font-size: 0.62rem;
          color: #687067;
          margin-top: 2px;
        }
        .demo-stage {
          padding: 38px;
          display: flex;
          flex-direction: column;
        }
        .demo-stage-index {
          display: flex;
          align-items: center;
          gap: 10px;
        }
        .demo-stage-index span {
          display: grid;
          place-items: center;
          width: 32px;
          height: 32px;
          border: 1px solid #172019;
          font-size: 0.7rem;
          font-weight: 900;
          background: #fbf9f4;
        }
        .demo-stage-index p {
          font-size: 0.62rem;
          font-weight: 900;
          letter-spacing: 0.12em;
          color: #0f5f4f;
          margin: 0;
        }
        .demo-stage h2 {
          font-size: clamp(2.2rem, 4vw, 3.6rem);
          line-height: 0.96;
          margin: 18px 0 14px;
          font-family: Georgia, serif;
        }
        .stage-lede {
          font-size: 0.95rem;
          line-height: 1.6;
          color: #495248;
          max-width: 720px;
        }
        .demo-output {
          margin: 22px 0;
          border: 1px solid #172019;
          background: #ffffff;
        }
        .demo-output-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 10px 14px;
          border-bottom: 1px solid #e2ded4;
          background: #fbf9f4;
          font-size: 0.62rem;
          font-weight: 850;
          letter-spacing: 0.1em;
          color: #687067;
        }
        .demo-facts {
          display: grid;
        }
        .demo-facts article {
          display: flex;
          align-items: center;
          gap: 10px;
          padding: 12px 14px;
          border-bottom: 1px solid #e2ded4;
        }
        .demo-facts article:last-child {
          border-bottom: 0;
        }
        .fact-bullet {
          color: #e84d7a;
          font-size: 1.2rem;
        }
        .demo-facts p {
          margin: 0;
          font-size: 0.82rem;
          color: #172019;
          font-weight: 650;
        }
        .report-evidence-grid,
        .signal-board-grid,
        .knowledge-evidence-grid {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 12px;
          margin-top: 18px;
        }
        .report-card,
        .signal-card,
        .know-card {
          padding: 16px;
          border: 1px solid #172019;
          background: #fbf9f4;
          display: flex;
          flex-direction: column;
          gap: 6px;
        }
        .card-tag,
        .signal-tag,
        .know-tag {
          font-size: 0.58rem;
          font-weight: 900;
          letter-spacing: 0.1em;
          color: #0f5f4f;
        }
        .report-card b,
        .signal-card b,
        .know-card b {
          font-size: 0.85rem;
          color: #172019;
        }
        .report-card small,
        .signal-card small,
        .know-card p {
          font-size: 0.72rem;
          color: #687067;
          margin: 0;
        }
        .review-demo-box {
          margin-top: 20px;
          padding: 22px;
          border: 1px solid #172019;
          background: #fff8dc;
          box-shadow: 4px 4px 0 #172019;
          display: flex;
          flex-direction: column;
          gap: 16px;
        }
        .review-tag {
          font-size: 0.6rem;
          font-weight: 900;
          letter-spacing: 0.1em;
          color: #e84d7a;
        }
        .review-info b {
          display: block;
          font-size: 1.05rem;
          font-family: Georgia, serif;
          margin: 6px 0;
        }
        .review-info p {
          font-size: 0.82rem;
          color: #384237;
          margin: 0;
          line-height: 1.5;
        }
        .review-actions-row {
          display: flex;
          gap: 10px;
        }
        .stage-footer-bar {
          margin-top: auto;
          padding-top: 24px;
          border-top: 1px solid #e2ded4;
          display: flex;
          justify-content: space-between;
          align-items: center;
        }
        .trace-info span {
          font-size: 0.58rem;
          font-weight: 850;
          letter-spacing: 0.1em;
          color: #687067;
          margin-right: 6px;
        }
        .trace-info code {
          font-size: 0.72rem;
          background: #fbf9f4;
          padding: 3px 6px;
          border: 1px solid #e2ded4;
        }
        .nav-buttons {
          display: flex;
          gap: 10px;
        }
        .prev-btn,
        .next-btn {
          padding: 8px 14px;
          border: 1px solid #172019;
          background: #ffffff;
          font-size: 0.75rem;
          font-weight: 750;
          cursor: pointer;
        }
        .prev-btn:disabled,
        .next-btn:disabled {
          opacity: 0.35;
          cursor: not-allowed;
        }
        @media (max-width: 850px) {
          .demo-grid {
            grid-template-columns: 1fr;
          }
          .demo-stepper {
            display: flex;
            overflow-x: auto;
            border-right: 0;
            border-bottom: 1px solid #172019;
          }
          .step-btn {
            min-width: 140px;
            grid-template-columns: 1fr;
          }
          .report-evidence-grid,
          .signal-board-grid,
          .knowledge-evidence-grid {
            grid-template-columns: 1fr;
          }
        }
      `}</style>
    </>
  );
}
