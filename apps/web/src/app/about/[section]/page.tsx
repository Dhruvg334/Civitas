"use client";

import { use } from "react";
import Link from "next/link";
import { Footer, Nav, SectionLabel } from "@/components/site";
import { FlatIcon } from "@/components/flat-icons";

interface Developer {
  name: string;
  role: string;
  techStack: string[];
  bio: string;
  github?: string;
}

const developers: Developer[] = [
  {
    name: "Dhruv Gupta",
    role: "Team Lead · System & Agentic Architecture",
    techStack: ["LangGraph", "FastAPI", "Groq", "PostgreSQL", "Next.js 16"],
    bio: "Leads Civitas end to end: product workflow, agentic analysis and decision orchestration, policy-grounded reasoning, frontend, cross-module contracts, final integration, deployment, and system validation.",
    github: "https://github.com/Dhruvg334",
  },
  {
    name: "Pavit Aggarwal",
    role: "Computer Vision & Geospatial ML",
    techStack: ["CLIP Zero-Shot", "PostGIS 3.4", "DBSCAN", "Python 3.12", "Scikit-Learn"],
    bio: "Engineered the multimodal vision pipeline, Before/After resolution verification model, spatial clustering algorithms, and risk calculation engines.",
    github: "https://github.com/pavitagrawal",
  },
  {
    name: "Utkarsh",
    role: "Backend Architecture & Municipal Operations",
    techStack: ["FastAPI", "PostgreSQL", "Pydantic", "Docker", "REST API Envelopes"],
    bio: "Built the FastAPI operational service, persistence layer, API contracts, municipal state transitions, work-order operations, and role-gated review flows.",
  },
];

export default function About({
  params,
}: {
  params: Promise<{ section: string }>;
}) {
  const { section } = use(params);

  if (section === "developers") {
    return (
      <>
        <Nav />
        <main className="about-main-shell">
          <SectionLabel index="03">EXPLORE / ENGINEERING TEAM</SectionLabel>
          <div className="about-hero-block">
            <h1 className="about-title">The Engineers Behind Civitas</h1>
            <p className="about-lead">
              Civitas is architected across agentic orchestration, computer vision, geospatial intelligence, and municipal backend systems.
            </p>
          </div>

          <section className="about-badge-card">
            <span className="badge-kicker">PRODUCTION ARCHITECTURE</span>
            <p>
              Civitas is an evidence-backed civic incident intelligence platform. Seeded data and live endpoints are explicitly distinguished to maintain strict engineering integrity.
            </p>
          </section>

          <section className="developers-grid">
            {developers.map((dev, index) => (
              <article key={dev.name} className="dev-profile-card">
                <div className="dev-card-top">
                  <span className="dev-index">0{index + 1}</span>
                  <div className="dev-role-badge">{dev.role}</div>
                </div>

                <h2 className="dev-name">{dev.name}</h2>
                <p className="dev-bio">{dev.bio}</p>

                <div className="dev-stack-pills">
                  {dev.techStack.map((tech) => (
                    <span key={tech} className="tech-pill">
                      {tech}
                    </span>
                  ))}
                </div>

                {dev.github ? (
                  <a
                    href={dev.github}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="dev-github-link"
                  >
                    View GitHub Profile ↗
                  </a>
                ) : null}
              </article>
            ))}
          </section>
        </main>
        <Footer />
        <AboutStyles />
      </>
    );
  }

  if (section === "why") {
    return (
      <>
        <Nav />
        <main className="about-main-shell">
          <SectionLabel index="02">EXPLORE / THE CIVIC PROBLEM</SectionLabel>
          <div className="about-hero-block">
            <h1 className="about-title">The Gap Between Citizen Reports & Municipal Action</h1>
            <p className="about-lead">
              Traditional 311 systems fail not from a lack of reports, but from unstructured noise, duplicate ticket inflation, and ungrounded response promises.
            </p>
          </div>

          <section className="problem-cards-grid">
            {[
              {
                num: "01",
                title: "Incomplete & Conflicting Resident Reports",
                desc: "Citizens describe issues in natural language without knowing municipal departmental codes. Three people describing the same water leak often report three different problems.",
              },
              {
                num: "02",
                title: "Duplicate Ticket Explosion",
                desc: "50 residents submitting reports for a single burst water main creates 50 separate tickets, overwhelming dispatch staff and obscuring real incident severity.",
              },
              {
                num: "03",
                title: "Severity Is Distinct From Priority",
                desc: "A moderate water leak outside a primary school gate during morning arrival poses greater civic urgency than a severe leak in an empty industrial lot. Spatial context is critical.",
              },
              {
                num: "04",
                title: "Policy Hallucination in Automated Bots",
                desc: "Standard LLM chatbots fabricate delivery timelines and invent municipal commitments. Civitas forces every recommendation to cite verified city playbooks (e.g. PLAY-WATER-01).",
              },
              {
                num: "05",
                title: "Citizen Transparency Void",
                desc: "Residents receive generic 'ticket logged' emails with zero updates on whether field crews arrived, how work orders progressed, or why a ticket was closed.",
              },
            ].map((prob) => (
              <article key={prob.num} className="problem-item-card">
                <span className="prob-num">{prob.num}</span>
                <h3>{prob.title}</h3>
                <p>{prob.desc}</p>
              </article>
            ))}
          </section>

          <div className="about-next-box">
            <div>
              <h3>Civitas bridges this operational gap.</h3>
              <p>Experience how multimodal evidence, PostGIS spatial clustering, and LangGraph work together.</p>
            </div>
            <Link className="button large" href="/workspace">
              Open Command Center →
            </Link>
          </div>
        </main>
        <Footer />
        <AboutStyles />
      </>
    );
  }

  // DEFAULT / "app" SECTION
  return (
    <>
      <Nav />
      <main className="about-main-shell">
        <SectionLabel index="01">EXPLORE / CIVITAS PLATFORM</SectionLabel>
        <div className="about-hero-block">
          <h1 className="about-title">Evidence-Backed Civic Incident Intelligence</h1>
          <p className="about-lead">
            Civitas transforms raw, noisy citizen submissions into verified spatial incidents, policy-grounded work orders, and reviewable field actions with human supervisor oversight.
          </p>
        </div>

        {/* SECTION 1: THE EVIDENCE TRIAD */}
        <section className="about-section-block">
          <div className="section-head-mini">
            <span className="section-sub-kicker">CORE GOVERNANCE PRINCIPLE</span>
            <h2>The Four Distinct Evidence Boundaries</h2>
            <p>
              Unlike traditional CRM systems that treat citizen text as blind execution instructions, Civitas maintains strict boundaries between evidence types:
            </p>
          </div>

          <div className="evidence-pillars-grid">
            <div className="evidence-pillar-card">
              <div className="pillar-num-badge">01</div>
              <h3>Observable Evidence (Media)</h3>
              <p>
                Visual artifacts (geotagged images, video clips) parsed through the vision pipeline and kept distinct from subjective descriptions and downstream inference.
              </p>
            </div>

            <div className="evidence-pillar-card">
              <div className="pillar-num-badge">02</div>
              <h3>Reported Claims (Citizen)</h3>
              <p>
                Natural language descriptions submitted by residents. Preserved faithfully without model overwriting, even when contradictory or ambiguous.
              </p>
            </div>

            <div className="evidence-pillar-card">
              <div className="pillar-num-badge">03</div>
              <h3>Retrieved Policy (Playbooks)</h3>
              <p>
                Authoritative municipal operating procedures (e.g. <code>PLAY-WATER-01</code>). LLM agents cite verified playbooks instead of inventing arbitrary timelines.
              </p>
            </div>

            <div className="evidence-pillar-card">
              <div className="pillar-num-badge">04</div>
              <h3>Deterministic Risk (PostGIS)</h3>
              <p>
                Spatial distance calculations to sensitive landmarks (schools, hospitals, transit arteries) and DBSCAN density clustering computed via PostGIS 3.4.
              </p>
            </div>
          </div>
        </section>

        {/* SECTION 2: FOR CITIZENS & SUPERVISORS */}
        <section className="about-dual-pillars">
          <article className="pillar-card resident">
            <span className="pillar-kicker">FOR CITIZENS & RESIDENTS</span>
            <h2>Report With Frictionless Ease</h2>
            <p>
              Describe what you see, snap a photo, and let our computer vision models structure the hazard. Track your report from intake to completed road repair.
            </p>
            <ul className="pillar-list">
              <li>
                <FlatIcon name="check" size={14} color="#0f5f4f" />
                <span>Instant landmark detection (e.g. &apos;Near DAV Public School&apos;).</span>
              </li>
              <li>
                <FlatIcon name="check" size={14} color="#0f5f4f" />
                <span>Real-time status checkpoints rather than email black holes.</span>
              </li>
              <li>
                <FlatIcon name="check" size={14} color="#0f5f4f" />
                <span>One-click clarification responses for field questions.</span>
              </li>
            </ul>
          </article>

          <article className="pillar-card municipal">
            <span className="pillar-kicker">FOR MUNICIPAL SUPERVISORS</span>
            <h2>Review Verified Decisions, Not Noise</h2>
            <p>
              Receive clustered incidents with severity scores, recommended departmental routing, and grounded playbooks ready for one-click authorization.
            </p>
            <ul className="pillar-list">
              <li>
                <FlatIcon name="check" size={14} color="#0f5f4f" />
                <span>50 duplicate reports consolidated into 1 operational incident.</span>
              </li>
              <li>
                <FlatIcon name="check" size={14} color="#0f5f4f" />
                <span>Before/after photo verification to prevent premature ticket closure.</span>
              </li>
              <li>
                <FlatIcon name="check" size={14} color="#0f5f4f" />
                <span>Complete LangGraph agent execution trace observability.</span>
              </li>
            </ul>
          </article>
        </section>

        {/* SECTION 3: PIPELINE FLOW BANNER */}
        <section className="pipeline-flow-banner">
          <div className="pipeline-node">
            <span>01</span>
            <b>CITIZEN REPORT</b>
          </div>
          <span className="node-sep">→</span>
          <div className="pipeline-node">
            <span>02</span>
            <b>POSTGIS CLUSTERING</b>
          </div>
          <span className="node-sep">→</span>
          <div className="pipeline-node">
            <span>03</span>
            <b>POLICY GROUNDING</b>
          </div>
          <span className="node-sep">→</span>
          <div className="pipeline-node">
            <span>04</span>
            <b>SUPERVISOR GATE</b>
          </div>
          <span className="node-sep">→</span>
          <div className="pipeline-node">
            <span>05</span>
            <b>FIELD ACTION</b>
          </div>
        </section>

        {/* SECTION 4: CALL TO ACTION */}
        <div className="about-next-box">
          <div>
            <h3>Ready to explore the Command Center?</h3>
            <p>Inspect real-time PostGIS clusters, review pending work orders, or test the evidence sandbox.</p>
          </div>
          <Link className="button large" href="/workspace">
            Open Workspace Command Center →
          </Link>
        </div>
      </main>
      <Footer />
      <AboutStyles />
    </>
  );
}

function AboutStyles() {
  return (
    <style jsx global>{`
      .about-main-shell {
        width: min(calc(100% - 40px), 1180px);
        margin: 36px auto 100px;
      }
      .about-hero-block {
        padding-bottom: 28px;
        border-bottom: 2px solid #172019;
        margin-bottom: 36px;
      }
      .about-title {
        font-size: clamp(2.4rem, 4.5vw, 4rem);
        font-family: Georgia, serif;
        margin: 8px 0 12px;
        color: #172019;
        line-height: 1;
      }
      .about-lead {
        font-size: 1.1rem;
        color: #555e54;
        max-width: 780px;
        line-height: 1.6;
        margin: 0;
      }
      .about-section-block {
        margin: 45px 0;
      }
      .section-head-mini {
        margin-bottom: 24px;
      }
      .section-sub-kicker {
        font-size: 0.65rem;
        font-weight: 900;
        letter-spacing: 0.12em;
        color: #0f5f4f;
        display: block;
        margin-bottom: 4px;
      }
      .section-head-mini h2 {
        font-size: 1.8rem;
        font-family: Georgia, serif;
        margin: 0 0 8px;
        color: #172019;
      }
      .section-head-mini p {
        font-size: 0.95rem;
        color: #555e54;
        max-width: 720px;
        line-height: 1.55;
        margin: 0;
      }
      .evidence-pillars-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 16px;
        margin-top: 18px;
      }
      .evidence-pillar-card {
        border: 1px solid #172019;
        background: #ffffff;
        padding: 22px;
        border-radius: 6px;
        box-shadow: 3px 3px 0 #172019;
        display: flex;
        flex-direction: column;
        gap: 6px;
      }
      .pillar-num-badge {
        width: 28px;
        height: 28px;
        border-radius: 50%;
        background: #172019;
        color: #ffffff;
        font-size: 0.72rem;
        font-weight: 900;
        display: grid;
        place-items: center;
        margin-bottom: 6px;
      }
      .evidence-pillar-card h3 {
        font-size: 1rem;
        font-family: Georgia, serif;
        margin: 0;
        color: #172019;
      }
      .evidence-pillar-card p {
        font-size: 0.8rem;
        color: #555e54;
        line-height: 1.5;
        margin: 0;
      }
      .about-badge-card {
        padding: 16px 20px;
        border: 1px dashed #0f5f4f;
        background: #f4f8f5;
        margin-bottom: 36px;
        border-radius: 4px;
      }
      .badge-kicker {
        font-size: 0.65rem;
        font-weight: 900;
        letter-spacing: 0.1em;
        color: #0f5f4f;
        display: block;
        margin-bottom: 4px;
      }
      .about-badge-card p {
        font-size: 0.85rem;
        color: #333f36;
        margin: 0;
        line-height: 1.5;
      }
      .developers-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 24px;
        margin-bottom: 45px;
      }
      .dev-profile-card {
        border: 2px solid #172019;
        background: #ffffff;
        padding: 24px;
        border-radius: 8px;
        box-shadow: 5px 5px 0 #172019;
        display: flex;
        flex-direction: column;
      }
      .dev-card-top {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        gap: 10px;
        margin-bottom: 16px;
      }
      .dev-index {
        font-size: 0.78rem;
        font-weight: 900;
        color: #e84d7a;
        flex-shrink: 0;
        padding-top: 3px;
      }
      .dev-role-badge {
        font-size: 0.65rem;
        font-weight: 850;
        padding: 4px 8px;
        background: #fbf9f4;
        border: 1px solid #172019;
        border-radius: 4px;
        line-height: 1.35;
        text-align: right;
        max-width: calc(100% - 32px);
      }
      .dev-name {
        font-size: 1.6rem;
        font-family: Georgia, serif;
        margin: 0 0 10px;
        color: #172019;
      }
      .dev-bio {
        font-size: 0.85rem;
        color: #555e54;
        line-height: 1.55;
        margin: 0 0 20px;
        flex: 1;
      }
      .dev-stack-pills {
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
        margin-bottom: 20px;
      }
      .tech-pill {
        padding: 3px 8px;
        border: 1px solid #e2ded4;
        background: #fbf9f4;
        font-size: 0.68rem;
        font-weight: 750;
        color: #0f5f4f;
        border-radius: 3px;
      }
      .dev-github-link {
        font-size: 0.8rem;
        font-weight: 850;
        color: #172019;
        text-decoration: none;
        padding-top: 12px;
        border-top: 1px solid #e2ded4;
      }
      .problem-cards-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 20px;
        margin-bottom: 45px;
      }
      .problem-item-card {
        border: 1px solid #172019;
        background: #ffffff;
        padding: 24px;
        border-radius: 6px;
        box-shadow: 4px 4px 0 #172019;
      }
      .prob-num {
        font-size: 0.72rem;
        font-weight: 900;
        color: #e84d7a;
        display: block;
        margin-bottom: 6px;
      }
      .problem-item-card h3 {
        font-size: 1.25rem;
        font-family: Georgia, serif;
        margin: 0 0 8px;
        color: #172019;
      }
      .problem-item-card p {
        font-size: 0.85rem;
        color: #555e54;
        line-height: 1.55;
        margin: 0;
      }
      .about-dual-pillars {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 24px;
        margin-bottom: 45px;
      }
      .pillar-card {
        border: 2px solid #172019;
        background: #ffffff;
        padding: 32px;
        border-radius: 8px;
        box-shadow: 5px 5px 0 #172019;
      }
      .pillar-kicker {
        font-size: 0.65rem;
        font-weight: 900;
        letter-spacing: 0.1em;
        color: #0f5f4f;
        display: block;
        margin-bottom: 8px;
      }
      .pillar-card h2 {
        font-size: 1.6rem;
        font-family: Georgia, serif;
        margin: 0 0 12px;
        color: #172019;
      }
      .pillar-card p {
        font-size: 0.9rem;
        color: #555e54;
        line-height: 1.55;
        margin: 0 0 20px;
      }
      .pillar-list {
        margin: 0;
        padding: 0;
        list-style: none;
        display: flex;
        flex-direction: column;
        gap: 10px;
      }
      .pillar-list li {
        font-size: 0.82rem;
        color: #172019;
        line-height: 1.45;
        display: flex;
        align-items: flex-start;
        gap: 8px;
      }
      .pipeline-flow-banner {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 24px 32px;
        border: 2px solid #172019;
        background: #172019;
        color: #ffffff;
        border-radius: 8px;
        margin-bottom: 45px;
        overflow-x: auto;
      }
      .pipeline-node {
        display: flex;
        flex-direction: column;
        gap: 4px;
      }
      .pipeline-node span {
        font-size: 0.65rem;
        font-weight: 900;
        color: #e84d7a;
      }
      .pipeline-node b {
        font-size: 0.82rem;
        letter-spacing: 0.08em;
      }
      .node-sep {
        font-size: 1.2rem;
        color: #0f5f4f;
        font-weight: 900;
      }
      .about-next-box {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 32px;
        border: 2px solid #172019;
        background: #fbf9f4;
        box-shadow: 5px 5px 0 #172019;
        border-radius: 8px;
        gap: 20px;
      }
      .about-next-box h3 {
        font-size: 1.4rem;
        font-family: Georgia, serif;
        margin: 0 0 6px;
        color: #172019;
      }
      .about-next-box p {
        font-size: 0.9rem;
        color: #555e54;
        margin: 0;
      }
      @media (max-width: 960px) {
        .developers-grid {
          grid-template-columns: 1fr;
        }
        .problem-cards-grid {
          grid-template-columns: 1fr;
        }
        .about-dual-pillars {
          grid-template-columns: 1fr;
        }
        .evidence-pillars-grid {
          grid-template-columns: 1fr 1fr;
        }
        .about-next-box {
          flex-direction: column;
          align-items: flex-start;
        }
      }
      @media (max-width: 600px) {
        .evidence-pillars-grid {
          grid-template-columns: 1fr;
        }
      }
    `}</style>
  );
}
