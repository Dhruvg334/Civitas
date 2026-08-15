"use client";

import { use } from "react";
import Link from "next/link";
import { Footer, Nav, SectionLabel } from "@/components/site";

interface Developer {
  name: string;
  role: string;
  techStack: string[];
  bio: string;
  github: string;
}

const developers: Developer[] = [
  {
    name: "Dhruv Gupta",
    role: "Product, Agentic AI & Orchestration",
    techStack: ["LangGraph", "FastAPI", "Groq AI", "PostgreSQL", "Next.js 16"],
    bio: "Leads product architecture, LangGraph state orchestration, municipal policy grounding, critic evaluation loops, and system verification.",
    github: "https://github.com/Dhruvg334",
  },
  {
    name: "Pavit Aggarwal",
    role: "Computer Vision, ML & Geospatial Intelligence",
    techStack: ["CLIP Zero-Shot", "PostGIS 3.4", "DBSCAN", "Python 3.12", "Scikit-Learn"],
    bio: "Engineered the multimodal vision pipeline, Before/After resolution verification model, spatial clustering algorithms, and risk calculation engines.",
    github: "https://github.com",
  },
  {
    name: "Utkarsh",
    role: "Backend Architecture & Municipal Operations",
    techStack: ["FastAPI", "PostgreSQL", "Pydantic", "Docker", "REST API Envelopes"],
    bio: "Constructed the high-throughput FastAPI service, persistence layer, supervisor review state machine, and citizen clarification routes.",
    github: "https://github.com",
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
          <SectionLabel index="03">ABOUT / ENGINEERING TEAM</SectionLabel>
          <div className="about-hero-block">
            <h1 className="about-title">The Engineers Behind Civitas</h1>
            <p className="about-lead">
              Civitas is architected across agentic orchestration, computer vision, geospatial intelligence, and municipal backend systems.
            </p>
          </div>

          <section className="about-badge-card">
            <span className="badge-kicker">EARLY HACKATHON MVP</span>
            <p>
              Civitas is an evidence-backed civic incident intelligence MVP. Seeded data and demo endpoints are explicitly distinguished from live municipal telemetry to maintain strict engineering integrity.
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

                <a
                  href={dev.github}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="dev-github-link"
                >
                  View GitHub Profile ↗
                </a>
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
          <SectionLabel index="02">ABOUT / THE CIVIC PROBLEM</SectionLabel>
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
            <Link className="button large" href="/demo-workflow">
              ⚡ Explore Workflow Demo
            </Link>
          </div>
        </main>
        <Footer />
        <AboutStyles />
      </>
    );
  }

  return (
    <>
      <Nav />
      <main className="about-main-shell">
        <SectionLabel index="01">ABOUT / APPLICATION ARCHITECTURE</SectionLabel>
        <div className="about-hero-block">
          <h1 className="about-title">A Civic Intelligence Platform Built on Evidence</h1>
          <p className="about-lead">
            Civitas turns raw, scattered citizen submissions into verified spatial incidents, policy-grounded work orders, and reviewable field actions.
          </p>
        </div>

        <section className="about-dual-pillars">
          <article className="pillar-card resident">
            <span className="pillar-kicker">FOR CITIZENS & RESIDENTS</span>
            <h2>Report With Frictionless Ease</h2>
            <p>
              Describe what you see, snap a photo, and let our computer vision models structure the hazard. Track your report from intake to completed road repair.
            </p>
              <ul className="pillar-list">
                <li>✓ Instant landmark detection (e.g. &apos;Near DAV Public School&apos;).</li>
                <li>✓ Real-time status checkpoints rather than email black holes.</li>
                <li>✓ One-click clarification responses for field questions.</li>
              </ul>
          </article>

          <article className="pillar-card municipal">
            <span className="pillar-kicker">FOR MUNICIPAL SUPERVISORS</span>
            <h2>Review Verified Decisions, Not Noise</h2>
            <p>
              Receive clustered incidents with severity scores, recommended departmental routing, and grounded playbooks ready for one-click authorization.
            </p>
            <ul className="pillar-list">
              <li>✓ 50 duplicate reports consolidated into 1 operational incident.</li>
              <li>✓ Before/after photo verification to prevent premature ticket closure.</li>
              <li>✓ Complete LangGraph agent execution trace observability.</li>
            </ul>
          </article>
        </section>

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
        font-size: 1.05rem;
        color: #555e54;
        margin: 0;
        max-width: 720px;
        line-height: 1.6;
      }
      .about-badge-card {
        padding: 16px 20px;
        border: 1px solid #0f5f4f;
        background: #f4f8f5;
        border-radius: 6px;
        margin-bottom: 36px;
      }
      .badge-kicker {
        font-size: 0.62rem;
        font-weight: 900;
        letter-spacing: 0.12em;
        color: #0f5f4f;
        display: block;
        margin-bottom: 4px;
      }
      .about-badge-card p {
        font-size: 0.88rem;
        color: #333f36;
        margin: 0;
        line-height: 1.5;
      }
      .developers-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 24px;
      }
      .dev-profile-card {
        border: 2px solid #172019;
        background: #ffffff;
        box-shadow: 4px 4px 0 #172019;
        padding: 24px;
        display: flex;
        flex-direction: column;
      }
      .dev-card-top {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 14px;
      }
      .dev-index {
        font-size: 0.75rem;
        font-weight: 900;
        font-family: monospace;
        color: #0f5f4f;
      }
      .dev-role-badge {
        font-size: 0.6rem;
        font-weight: 900;
        background: #172019;
        color: #ffffff;
        padding: 2px 6px;
        border-radius: 3px;
      }
      .dev-name {
        font-size: 1.4rem;
        font-family: Georgia, serif;
        margin: 0 0 8px;
        color: #172019;
      }
      .dev-bio {
        font-size: 0.85rem;
        color: #555e54;
        line-height: 1.5;
        margin: 0 0 18px;
        flex: 1;
      }
      .dev-stack-pills {
        display: flex;
        gap: 6px;
        flex-wrap: wrap;
        margin-bottom: 18px;
      }
      .tech-pill {
        font-size: 0.65rem;
        font-weight: 800;
        background: #fbf9f4;
        border: 1px solid #e2ded4;
        padding: 2px 6px;
        border-radius: 3px;
        color: #495248;
      }
      .dev-github-link {
        font-size: 0.78rem;
        font-weight: 800;
        color: #0f5f4f;
        text-decoration: none;
        transition: color 0.15s ease;
      }
      .dev-github-link:hover {
        color: #e84d7a;
      }
      .problem-cards-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 20px;
        margin-bottom: 40px;
      }
      .problem-item-card {
        border: 1px solid #172019;
        background: #ffffff;
        padding: 24px;
        box-shadow: 3px 3px 0 #172019;
      }
      .prob-num {
        font-size: 0.85rem;
        font-weight: 900;
        color: #e84d7a;
        font-family: monospace;
        display: block;
        margin-bottom: 8px;
      }
      .problem-item-card h3 {
        font-size: 1.15rem;
        font-family: Georgia, serif;
        margin: 0 0 8px;
        color: #172019;
      }
      .problem-item-card p {
        font-size: 0.85rem;
        color: #555e54;
        line-height: 1.5;
        margin: 0;
      }
      .about-next-box {
        border: 2px solid #172019;
        background: #fbf9f4;
        padding: 32px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 6px 6px 0 #172019;
        gap: 20px;
        flex-wrap: wrap;
      }
      .about-next-box h3 {
        font-size: 1.4rem;
        font-family: Georgia, serif;
        margin: 0 0 4px;
        color: #172019;
      }
      .about-next-box p {
        font-size: 0.9rem;
        color: #555e54;
        margin: 0;
      }
      .about-dual-pillars {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 28px;
        margin-bottom: 40px;
      }
      .pillar-card {
        border: 2px solid #172019;
        padding: 32px;
        box-shadow: 4px 4px 0 #172019;
      }
      .pillar-card.resident {
        background: #ffffff;
      }
      .pillar-card.municipal {
        background: #f4f8f5;
        border-color: #0f5f4f;
      }
      .pillar-kicker {
        font-size: 0.62rem;
        font-weight: 900;
        letter-spacing: 0.12em;
        color: #0f5f4f;
        display: block;
        margin-bottom: 6px;
      }
      .pillar-card h2 {
        font-size: 1.6rem;
        font-family: Georgia, serif;
        margin: 0 0 10px;
        color: #172019;
      }
      .pillar-card p {
        font-size: 0.9rem;
        color: #555e54;
        line-height: 1.55;
        margin: 0 0 18px;
      }
      .pillar-list {
        margin: 0;
        padding: 0;
        list-style: none;
        display: flex;
        flex-direction: column;
        gap: 8px;
      }
      .pillar-list li {
        font-size: 0.85rem;
        color: #333f36;
      }
      .pipeline-flow-banner {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: #172019;
        color: #ffffff;
        padding: 24px 32px;
        border-radius: 6px;
        flex-wrap: wrap;
        gap: 12px;
      }
      .pipeline-node {
        display: flex;
        flex-direction: column;
        gap: 2px;
      }
      .pipeline-node span {
        font-size: 0.65rem;
        font-weight: 900;
        color: #dce8dd;
        font-family: monospace;
      }
      .pipeline-node b {
        font-size: 0.82rem;
        letter-spacing: 0.08em;
      }
      .node-sep {
        font-size: 1.2rem;
        color: #e84d7a;
      }
      @media (max-width: 900px) {
        .developers-grid {
          grid-template-columns: 1fr;
        }
        .problem-cards-grid {
          grid-template-columns: 1fr;
        }
        .about-dual-pillars {
          grid-template-columns: 1fr;
        }
        .pipeline-flow-banner {
          flex-direction: column;
          align-items: flex-start;
        }
        .node-sep {
          display: none;
        }
      }
    `}</style>
  );
}
