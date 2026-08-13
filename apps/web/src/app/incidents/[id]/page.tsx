import type { Metadata } from "next";
import { ReviewPanel } from "@/components/review-panel";
import { ResolutionSlider } from "@/components/resolution-slider";
import { AgentTraceVisualizer } from "@/components/agent-trace-visualizer";
import { ErrorBoundary } from "@/components/error-boundary";
import { Nav, Status, Footer } from "@/components/site";

export const metadata: Metadata = {
  title: "Incident INC-0241 — School Crossing Water Leak",
  description:
    "Evidence-backed operational record for water leakage incident near school crossing with grounded work order and resolution verification.",
};

export default function Incident() {
  return (
    <>
      <Nav />
      <main className="incident-shell">
        <header className="incident-top">
          <div>
            <span className="workspace-kicker">INC-0241 / WATER LEAKAGE</span>
            <h1>Water leak near school crossing</h1>
            <p>
              Three related resident reports (photo, text, video) consolidated into one verified
              operational incident.
            </p>
          </div>
          <div className="incident-state">
            <Status tone="warn">WAITING_FOR_REVIEW</Status>
            <small>Trace ID: CIV-TR-0241</small>
          </div>
        </header>

        <nav className="incident-tabs" aria-label="Incident sections">
          <a href="#evidence">01 Evidence</a>
          <a href="#assessment">02 Risk Assessment</a>
          <a href="#routing">03 Routing & Plan</a>
          <a href="#resolution">04 Resolution Verification</a>
          <a href="#trace">05 Agent Trace</a>
          <a href="#review">06 Review Gate</a>
        </nav>

        <div className="incident-layout">
          <section className="incident-content">
            {/* SECTION 01: EVIDENCE */}
            <section id="evidence" className="incident-section">
              <div className="section-title">
                <span>01</span>
                <h2>Multimodal Evidence & Claims</h2>
                <p>Observed evidence is distinguished from reported resident claims.</p>
              </div>

              <div className="evidence-grid">
                <article>
                  <span className="evidence-kind observed">OBSERVED EVIDENCE</span>
                  <b>Standing water crosses part of the roadway.</b>
                  <p>Computer vision verified active water flow across road surface (frame-002).</p>
                </article>
                <article>
                  <span className="evidence-kind reported">CITIZEN REPORTED</span>
                  <b>Bikes are slipping near the school gate.</b>
                  <p>Citizen text claim, retained as safety landmark context.</p>
                </article>
                <article>
                  <span className="evidence-kind inferred">UNVERIFIED INFERENCE</span>
                  <b>Leak origin is an underground pipe rupture.</b>
                  <p>Field inspection required before confirming infrastructure source.</p>
                </article>
              </div>

              <div className="report-sources">
                <span>REPORT A · PHOTO (20.2961, 85.8245)</span>
                <span>REPORT B · TEXT (School Landmark)</span>
                <span>REPORT C · VIDEO (Citizen Category: Pothole → Corrected)</span>
              </div>
            </section>

            {/* SECTION 02: ASSESSMENT */}
            <section id="assessment" className="incident-section">
              <div className="section-title">
                <span>02</span>
                <h2>Severity & Priority Intelligence</h2>
                <p>Deterministic models evaluate physical impact separately from response priority.</p>
              </div>

              <div className="assessment-board">
                <div>
                  <span>Category</span>
                  <b>Water leakage</b>
                  <small>Citizen category corrected automatically</small>
                </div>
                <div>
                  <span>Duplicate Cluster</span>
                  <b>3 Related Reports</b>
                  <small>Multimodal similarity 0.84 (Threshold 0.72)</small>
                </div>
                <div>
                  <span>Severity Score</span>
                  <b>78 / 100 · High</b>
                  <small>Active road flooding & slip risk factors</small>
                </div>
                <div>
                  <span>Priority Level</span>
                  <b>P1 · Critical</b>
                  <small>School proximity + traffic exposure</small>
                </div>
              </div>
            </section>

            {/* SECTION 03: ROUTING & WORK ORDER */}
            <section id="routing" className="incident-section">
              <div className="section-title">
                <span>03</span>
                <h2>Policy-Grounded Routing & Plan</h2>
                <p>Operational work order compiled from municipal playbooks.</p>
              </div>

              <div className="routing-line">
                <div>
                  <span>PRIMARY JURISDICTION</span>
                  <b>Water Supply Department</b>
                </div>
                <i>→</i>
                <div><span>SECONDARY COORDINATION</span><b>Traffic Operations</b></div>
              </div>

              <div className="work-order">
                <span>WORK ORDER DRAFT (WO-0241-A)</span>
                <h3>Inspect and isolate the active leak; make the affected crossing safe.</h3>
                <ul>
                  <li>Confirm leak source on site near East Gate.</li>
                  <li>Secure the affected road section with safety barriers.</li>
                  <li>Coordinate traffic handling while inspection is underway.</li>
                  <li>Non-binding estimated resolution window: 8 – 14 hours.</li>
                </ul>
                <footer>
                  <b>Grounded by Municipal Policy PLAY-WATER-01 & ROUTE-WATER-02</b>
                  <span>Requires Human Review Sign-off</span>
                </footer>
              </div>
            </section>

            {/* SECTION 04: RESOLUTION VERIFICATION */}
            <section id="resolution" className="incident-section">
              <div className="section-title">
                <span>04</span>
                <h2>Before / After Resolution Verification</h2>
                <p>Visual classification of initial vs. completed field work evidence.</p>
              </div>
              <ErrorBoundary>
                <ResolutionSlider />
              </ErrorBoundary>
            </section>

            {/* SECTION 05: AGENT TRACE VISUALIZER */}
            <section id="trace" className="incident-section">
              <div className="section-title">
                <span>05</span>
                <h2>LangGraph Agent Workflow Observability</h2>
                <p>Inspect node-by-node execution, latency metrics, and critic gates.</p>
              </div>
              <ErrorBoundary>
                <AgentTraceVisualizer />
              </ErrorBoundary>
            </section>
          </section>

          {/* ASIDE / STICKY REVIEW PANEL */}
          <aside className="incident-aside">
            <div className="sticky-review" id="review">
              <ErrorBoundary>
                <ReviewPanel />
              </ErrorBoundary>
            </div>
          </aside>
        </div>
      </main>
      <Footer />
    </>
  );
}
