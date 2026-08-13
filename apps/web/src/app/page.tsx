"use client";

import Link from "next/link";
import { LandingExplorer } from "@/components/landing-explorer";
import { Footer, Nav, SectionLabel } from "@/components/site";

export default function Home() {
  return (
    <>
      <Nav />
      <main className="home">
        {/* FULLSCREEN HERO SECTION */}
        <section className="hero-fullscreen">
          <div className="hero-content">
            <span className="hero-kicker">CIVIC INCIDENT INTELLIGENCE</span>
            <h1 className="hero-title">Civitas</h1>
            <p className="hero-tagline">
              Turn every civic report into a clear, evidence-backed path to action.
            </p>

            <div className="actions hero-actions">
              <Link className="button hero-button-primary" href="/report">
                Report an issue
              </Link>
              <Link className="outline hero-button-secondary" href="/demo-workflow">
                Explore the live demo
              </Link>
            </div>

            <p className="hero-note">
              Human-reviewed. Policy-grounded. Built for municipal operations.
            </p>
          </div>

          <div className="scroll-indicator" aria-hidden="true">
            <span>SCROLL TO EXPLORE WORKFLOW</span>
            <i className="arrow-down">↓</i>
          </div>
        </section>

        {/* 3 CONNECTED CAPABILITIES SECTION */}
        <LandingExplorer />

        {/* WORKFLOW IN PRACTICE SECTION */}
        <section className="workflow-story compact-story">
          <SectionLabel index="04">THE WORKFLOW IN PRACTICE</SectionLabel>
          <div className="story-heading">
            <h2>Not another inbox. A shared operational picture.</h2>
            <p>
              Reports arrive through ordinary citizen language. Civitas turns fragmented input into
              a carefully bounded decision, retaining what was observed, reported, retrieved, and inferred.
            </p>
          </div>

          <div className="workflow-steps">
            <article className="step-card">
              <span className="step-num">01</span>
              <h3>Collect</h3>
              <p>
                Text, media, location, and resident context become an incident-ready operational record.
              </p>
              <span className="step-badge">MULTIMODAL INTAKE</span>
            </article>

            <article className="step-card">
              <span className="step-num">02</span>
              <h3>Understand</h3>
              <p>
                Computer vision, duplicate detection, and severity tools calculate similarity and physical risk.
              </p>
              <span className="step-badge">DETERMINISTIC ML</span>
            </article>

            <article className="step-card">
              <span className="step-num">03</span>
              <h3>Decide</h3>
              <p>
                Policy-grounded routing and work orders are checked, traced, and presented for supervisor approval.
              </p>
              <span className="step-badge">HUMAN APPROVAL GATE</span>
            </article>
          </div>
        </section>

        {/* CLOSING CTA SECTION */}
        <section className="closing-cta">
          <div className="cta-copy">
            <p className="section-kicker">BUILT FOR THE HANDOFF</p>
            <h2>Bring the right context to the people who act on it.</h2>
            <p>
              Walk through the seeded water-leak scenario to see three distinct resident reports
              become one accountable municipal work order.
            </p>
          </div>
          <div className="cta-actions">
            <Link className="button secondary" href="/demo-workflow">
              Open the Workflow Demo
            </Link>
          </div>
        </section>
      </main>
      <Footer />

      <style jsx>{`
        .hero-fullscreen {
          min-height: calc(100vh - 74px);
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          position: relative;
          text-align: center;
          padding: 2rem 1rem;
          box-sizing: border-box;
        }
        .hero-content {
          max-width: 860px;
          margin: auto 0;
        }
        .hero-kicker {
          display: inline-block;
          margin-bottom: 0.75rem;
          color: #0f5f4f;
          font-size: 0.75rem;
          font-weight: 850;
          letter-spacing: 0.14em;
        }
        .hero-title {
          font-size: clamp(4.5rem, 10vw, 8.5rem);
          line-height: 0.85;
          margin: 0.25rem 0 1.25rem;
          font-family: Georgia, "Times New Roman", serif;
          letter-spacing: -0.04em;
          color: #172019;
        }
        .hero-tagline {
          max-width: 660px;
          margin: 0 auto 2rem;
          font-family: Georgia, serif;
          font-size: clamp(1.25rem, 2.5vw, 1.95rem);
          line-height: 1.25;
          color: #384237;
        }
        .hero-actions {
          display: flex;
          justify-content: center;
          gap: 1.25rem;
          margin-bottom: 1.5rem;
        }
        .hero-button-primary {
          padding: 14px 24px !important;
          font-size: 0.95rem !important;
        }
        .hero-button-secondary {
          padding: 13px 22px !important;
          font-size: 0.95rem !important;
        }
        .scroll-indicator {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 4px;
          font-size: 0.65rem;
          font-weight: 850;
          letter-spacing: 0.12em;
          color: #687067;
          margin-top: auto;
          padding-bottom: 1.25rem;
        }
        .arrow-down {
          font-style: normal;
          font-size: 1.1rem;
          animation: bounce 2s infinite;
        }
        .step-card {
          position: relative;
          background: #fffdf7;
          padding: 2rem;
          border: 1px solid #172019;
          box-shadow: 4px 4px 0 #172019;
          transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        .step-card:hover {
          transform: translateY(-4px);
          box-shadow: 6px 6px 0 #0f5f4f;
        }
        .step-num {
          font-size: 0.75rem;
          font-weight: 900;
          color: #e84d7a;
          display: block;
          margin-bottom: 0.75rem;
        }
        .step-badge {
          display: inline-block;
          margin-top: 1.25rem;
          font-size: 0.6rem;
          font-weight: 850;
          letter-spacing: 0.1em;
          color: #0f5f4f;
          padding: 3px 8px;
          background: #dce8dd;
          border: 1px solid #0f5f4f;
        }
        .cta-actions {
          flex: none;
        }
        @keyframes bounce {
          0%, 20%, 50%, 80%, 100% { transform: translateY(0); }
          40% { transform: translateY(6px); }
          60% { transform: translateY(3px); }
        }
      `}</style>
    </>
  );
}
