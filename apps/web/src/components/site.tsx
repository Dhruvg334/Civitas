"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { AboutMenu } from "@/components/about-menu";
import { CookieControls } from "@/components/cookie-controls";

const productLinks: Array<[string, string]> = [
  ["Workspace", "/workspace"],
  ["Demo", "/demo-workflow"],
  ["Docs", "/docs"],
  ["Profile", "/profile"],
];

const docsNavTabs: Array<{ label: string; href: string; slug: string }> = [
  { label: "Overview", href: "/docs", slug: "" },
  { label: "System Architecture", href: "/docs/architecture", slug: "architecture" },
  { label: "Operations & Workflow", href: "/docs/workflow", slug: "workflow" },
  { label: "Governance & Safety", href: "/docs/safety", slug: "safety" },
  { label: "API Reference", href: "/docs/api", slug: "api" },
];

const aboutLinks: Array<[string, string]> = [
  ["About App", "/about/app"],
  ["Why It Is Needed", "/about/why"],
  ["Team behind", "/about/developers"],
];

function Wordmark() {
  return (
    <Link className="brand" href="/" aria-label="Civitas home">
      <span className="brand-mark" aria-hidden="true">
        <i />
        <i />
        <i />
      </span>
      <span>Civitas</span>
    </Link>
  );
}

export function Nav({ docs = false }: { docs?: boolean } = {}) {
  const pathname = usePathname() || "";

  const isLinkActive = (href: string) => {
    if (href === "/") return pathname === "/";
    if (href === "/profile") return pathname.startsWith("/profile") || pathname.startsWith("/sign-in");
    if (href === "/workspace") return pathname.startsWith("/workspace") || pathname.startsWith("/incidents");
    return pathname.startsWith(href);
  };

  const isAboutActive = pathname.startsWith("/about");
  const isReportActive = pathname.startsWith("/report");

  return (
    <>
      <header className="site-header">
        <nav className="nav" aria-label="Primary navigation">
          <Wordmark />
          <div className="nav-center">
            {productLinks.map(([label, href]) => {
              const active = isLinkActive(href);
              return (
                <Link
                  key={href}
                  href={href}
                  className={active ? "active" : ""}
                  aria-current={active ? "page" : undefined}
                >
                  {label}
                </Link>
              );
            })}
            <AboutMenu isActive={isAboutActive} />
          </div>
          <div className="nav-end">
            <Link
              className={`button small ${isReportActive ? "active-button" : ""}`}
              href="/report"
            >
              Report an issue
            </Link>
            <details className="mobilemenu">
              <summary aria-label="Open navigation">
                <span />
                <span />
              </summary>
              <div>
                {productLinks.map(([label, href]) => (
                  <Link
                    key={href}
                    href={href}
                    className={isLinkActive(href) ? "active" : ""}
                  >
                    {label}
                  </Link>
                ))}
                {aboutLinks.map(([label, href]) => (
                  <Link
                    key={href}
                    href={href}
                    className={pathname.startsWith(href) ? "active" : ""}
                  >
                    {label}
                  </Link>
                ))}
              </div>
            </details>
          </div>
        </nav>
      </header>
      {docs && <DocsSubNav />}
    </>
  );
}

export function DocsSubNav({
  activeSlug = "",
  onSearchChange,
}: {
  activeSlug?: string;
  onSearchChange?: (q: string) => void;
}) {
  const pathname = usePathname() || "";
  const [searchTerm, setSearchTerm] = useState("");

  const handleSearch = (val: string) => {
    setSearchTerm(val);
    if (onSearchChange) onSearchChange(val);
  };

  return (
    <div className="docs-subnav-ribbon" aria-label="Documentation section navigation">
      <div className="docs-subnav-inner">
        <div className="docs-nav-tabs">
          {docsNavTabs.map((tab) => {
            const isTabActive =
              tab.slug === ""
                ? pathname === "/docs"
                : pathname === tab.href || activeSlug === tab.slug;

            return (
              <Link
                key={tab.href}
                href={tab.href}
                className={`docs-tab-link ${isTabActive ? "active" : ""}`}
              >
                {tab.label}
              </Link>
            );
          })}
        </div>

        <div className="docs-subnav-right">
          <div className="docs-search-wrapper">
            <span className="search-icon">🔍</span>
            <input
              type="text"
              placeholder="Filter topics & schemas..."
              value={searchTerm}
              onChange={(e) => handleSearch(e.target.value)}
              className="docs-search-input"
              aria-label="Filter documentation"
            />
          </div>
          <span className="docs-version-pill">v0.1.0-alpha · LangGraph</span>
        </div>
      </div>

      <style jsx>{`
        .docs-subnav-ribbon {
          border-bottom: 1px solid #172019;
          background: #ffffff;
          position: sticky;
          top: 74px;
          z-index: 40;
          box-shadow: 0 2px 6px rgba(0, 0, 0, 0.04);
        }
        .docs-subnav-inner {
          width: min(calc(100% - 40px), 1280px);
          margin: 0 auto;
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 0;
          gap: 20px;
        }
        .docs-nav-tabs {
          display: flex;
          align-items: center;
          gap: 0;
          overflow-x: auto;
        }
        .docs-tab-link {
          padding: 14px 18px;
          border-right: 1px solid #e2ded4;
          font-size: 0.8rem;
          font-weight: 750;
          color: #555e54;
          text-decoration: none;
          white-space: nowrap;
          transition: all 0.15s ease;
        }
        .docs-tab-link:first-child {
          border-left: 1px solid #e2ded4;
        }
        .docs-tab-link:hover {
          color: #172019;
          background: #fbf9f4;
        }
        .docs-tab-link.active {
          color: #ffffff;
          background: #172019;
        }
        .docs-subnav-right {
          display: flex;
          align-items: center;
          gap: 14px;
        }
        .docs-search-wrapper {
          display: flex;
          align-items: center;
          gap: 6px;
          background: #fbf9f4;
          border: 1px solid #172019;
          padding: 5px 10px;
          border-radius: 4px;
        }
        .search-icon {
          font-size: 0.75rem;
        }
        .docs-search-input {
          border: 0;
          background: transparent;
          font-size: 0.78rem;
          outline: none;
          width: 170px;
        }
        .docs-version-pill {
          font-size: 0.65rem;
          font-weight: 850;
          background: #dce8dd;
          color: #0f5f4f;
          padding: 4px 8px;
          border: 1px solid #0f5f4f;
          border-radius: 4px;
          white-space: nowrap;
        }
        @media (max-width: 900px) {
          .docs-subnav-inner {
            flex-direction: column;
            align-items: stretch;
            padding: 8px 0;
          }
          .docs-subnav-right {
            justify-content: space-between;
          }
          .docs-search-input {
            width: 100%;
          }
        }
      `}</style>
    </div>
  );
}

export function Footer() {
  return (
    <footer className="footer-grid-shell">
      <div className="footer-content">
        <div className="footer-col brand-col">
          <Link className="brand footer-brand" href="/">
            <span className="brand-mark" aria-hidden="true">
              <i />
              <i />
              <i />
            </span>
            <span>Civitas</span>
          </Link>
          <p className="footer-tagline">
            Evidence-backed civic incident intelligence with human oversight.
          </p>
          <div className="footer-status-pill">
            <span className="live-dot" />
            <span>OPERATIONAL · POSTGIS ENABLED</span>
          </div>
        </div>

        <div className="footer-col">
          <span className="footer-heading">PRODUCT</span>
          <Link href="/workspace">Command Center</Link>
          <Link href="/demo-workflow">Workflow Demo</Link>
          <Link href="/report">Report Issue</Link>
          <Link href="/docs">System Docs</Link>
        </div>

        <div className="footer-col">
          <span className="footer-heading">GOVERNANCE</span>
          <Link href="/about/app">About Civitas</Link>
          <Link href="/docs/architecture">Architecture</Link>
          <Link href="/privacy">Privacy & Location</Link>
          <Link href="/terms">Terms of Use</Link>
        </div>

        <div className="footer-col">
          <span className="footer-heading">ACCOUNT</span>
          <Link href="/profile">Resident Profile</Link>
          <Link href="/sign-in">Sign In / Register</Link>
          <div className="footer-cookie-wrapper">
            <CookieControls />
          </div>
        </div>
      </div>

      <div className="footer-bottom">
        <p>© 2026 Civitas Platform. Open civic incident intelligence with human oversight.</p>
      </div>

      <style jsx>{`
        .footer-grid-shell {
          border-top: 1px solid #172019;
          background: #fbf9f4;
          padding: 55px 0 35px;
          margin-top: auto;
        }
        .footer-content {
          width: min(calc(100% - 40px), 1180px);
          margin: 0 auto;
          display: grid;
          grid-template-columns: 1.4fr 1fr 1fr 1fr;
          gap: 40px;
          padding-bottom: 40px;
          border-bottom: 1px solid #e2ded4;
        }
        .brand-col {
          display: flex;
          flex-direction: column;
          gap: 12px;
        }
        .footer-tagline {
          font-size: 0.85rem;
          color: #555e54;
          line-height: 1.55;
          max-width: 320px;
          margin: 0;
        }
        .footer-status-pill {
          display: inline-flex;
          align-items: center;
          gap: 8px;
          padding: 4px 9px;
          border: 1px solid #172019;
          background: #ffffff;
          font-size: 0.6rem;
          font-weight: 850;
          letter-spacing: 0.08em;
          width: max-content;
          margin-top: 6px;
        }
        .footer-col {
          display: flex;
          flex-direction: column;
          gap: 10px;
        }
        .footer-heading {
          font-size: 0.65rem;
          font-weight: 900;
          letter-spacing: 0.12em;
          color: #0f5f4f;
          margin-bottom: 4px;
        }
        .footer-col :global(a) {
          font-size: 0.84rem;
          font-weight: 700;
          color: #172019;
          transition: color 0.15s ease;
          text-decoration: none;
        }
        .footer-col :global(a:hover) {
          color: #e84d7a;
        }
        .footer-cookie-wrapper {
          margin-top: 6px;
        }
        .footer-bottom {
          width: min(calc(100% - 40px), 1180px);
          margin: 25px auto 0;
          display: flex;
          justify-content: space-between;
          align-items: center;
          font-size: 0.75rem;
          color: #687067;
        }
        .footer-bottom p {
          margin: 0;
        }
        @media (max-width: 800px) {
          .footer-content {
            grid-template-columns: 1fr 1fr;
            gap: 30px;
          }
        }
        @media (max-width: 500px) {
          .footer-content {
            grid-template-columns: 1fr;
          }
        }
      `}</style>
    </footer>
  );
}

export function Status({
  children,
  tone = "neutral",
}: {
  children: string;
  tone?: "neutral" | "good" | "warn" | "danger";
}) {
  return (
    <span className={`status status-${tone}`}>
      <i aria-hidden="true" />
      {children.replaceAll("_", " ").toLowerCase()}
    </span>
  );
}

export function SectionLabel({
  index,
  children,
}: {
  index?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="section-label">
      {index && <span>{index}</span>}
      <p>{children}</p>
    </div>
  );
}

export function DocsPage({
  title,
  intro,
  activeSlug = "",
  tocItems = [],
  children,
}: {
  title: string;
  intro?: string;
  activeSlug?: string;
  tocItems?: Array<{ id: string; label: string }>;
  children: React.ReactNode;
}) {
  const [, setSearchFilter] = useState("");

  return (
    <>
      <Nav />
      <DocsSubNav activeSlug={activeSlug} onSearchChange={setSearchFilter} />
      <main className="docs-dual-layout">
        {/* LEFT TOPIC SIDEBAR */}
        <aside className="docs-left-sidebar" aria-label="Documentation topics">
          <div className="sidebar-group">
            <span className="sidebar-group-title">GETTING STARTED</span>
            <Link href="/docs" className={activeSlug === "" ? "active" : ""}>
              📄 System Overview
            </Link>
            <Link href="/docs/architecture" className={activeSlug === "architecture" ? "active" : ""}>
              🏗️ System Architecture
            </Link>
          </div>

          <div className="sidebar-group">
            <span className="sidebar-group-title">OPERATIONS & AI</span>
            <Link href="/docs/workflow" className={activeSlug === "workflow" ? "active" : ""}>
              ⚡ Workflow & Operations
            </Link>
            <Link href="/docs/safety" className={activeSlug === "safety" ? "active" : ""}>
              🛡️ Governance & Safety
            </Link>
          </div>

          <div className="sidebar-group">
            <span className="sidebar-group-title">INTEGRATION</span>
            <Link href="/docs/api" className={activeSlug === "api" ? "active" : ""}>
              🔌 REST API Reference
            </Link>
          </div>
        </aside>

        {/* CENTER MAIN ARTICLE */}
        <article className="docs-main-article">
          <div className="docs-header-block">
            <span className="doc-eyebrow">CIVITAS DOCUMENTATION / {activeSlug.toUpperCase() || "OVERVIEW"}</span>
            <h1 className="doc-main-title">{title}</h1>
            {intro && <p className="doc-main-intro">{intro}</p>}
          </div>

          <div className="doc-content-body">{children}</div>
        </article>

        {/* RIGHT TABLE OF CONTENTS */}
        {tocItems.length > 0 && (
          <aside className="docs-right-toc" aria-label="Table of contents">
            <span className="toc-title">ON THIS PAGE</span>
            <div className="toc-links">
              {tocItems.map((item) => (
                <a key={item.id} href={`#${item.id}`}>
                  {item.label}
                </a>
              ))}
            </div>
          </aside>
        )}
      </main>
      <Footer />

      <style jsx>{`
        .docs-dual-layout {
          width: min(calc(100% - 40px), 1280px);
          margin: 36px auto 100px;
          display: grid;
          grid-template-columns: 220px minmax(0, 1fr) 200px;
          gap: 45px;
          align-items: start;
        }
        .docs-left-sidebar {
          position: sticky;
          top: 140px;
          display: flex;
          flex-direction: column;
          gap: 24px;
          border-right: 1px solid #e2ded4;
          padding-right: 20px;
        }
        .sidebar-group {
          display: flex;
          flex-direction: column;
          gap: 6px;
        }
        .sidebar-group-title {
          font-size: 0.62rem;
          font-weight: 900;
          letter-spacing: 0.12em;
          color: #0f5f4f;
          margin-bottom: 4px;
        }
        .sidebar-group :global(a) {
          padding: 6px 10px;
          font-size: 0.82rem;
          font-weight: 750;
          color: #555e54;
          text-decoration: none;
          border-radius: 4px;
          transition: all 0.15s ease;
        }
        .sidebar-group :global(a:hover) {
          color: #172019;
          background: #fbf9f4;
        }
        .sidebar-group :global(a.active) {
          color: #ffffff;
          background: #172019;
        }
        .docs-main-article {
          min-width: 0;
        }
        .docs-header-block {
          padding-bottom: 28px;
          border-bottom: 2px solid #172019;
          margin-bottom: 32px;
        }
        .doc-eyebrow {
          font-size: 0.65rem;
          font-weight: 900;
          letter-spacing: 0.14em;
          color: #0f5f4f;
          display: block;
          margin-bottom: 6px;
        }
        .doc-main-title {
          font-size: clamp(2.6rem, 4.5vw, 4.2rem);
          line-height: 0.94;
          margin: 0 0 14px;
          font-family: Georgia, serif;
          color: #172019;
        }
        .doc-main-intro {
          font-size: 1.05rem;
          line-height: 1.6;
          color: #495248;
          margin: 0;
        }
        .docs-right-toc {
          position: sticky;
          top: 140px;
          border-left: 1px solid #e2ded4;
          padding-left: 18px;
          display: flex;
          flex-direction: column;
          gap: 10px;
        }
        .toc-title {
          font-size: 0.62rem;
          font-weight: 900;
          letter-spacing: 0.12em;
          color: #687067;
        }
        .toc-links {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }
        .toc-links a {
          font-size: 0.78rem;
          color: #555e54;
          text-decoration: none;
          line-height: 1.4;
          transition: color 0.15s ease;
        }
        .toc-links a:hover {
          color: #e84d7a;
        }
        @media (max-width: 1050px) {
          .docs-dual-layout {
            grid-template-columns: 200px minmax(0, 1fr);
          }
          .docs-right-toc {
            display: none;
          }
        }
        @media (max-width: 768px) {
          .docs-dual-layout {
            grid-template-columns: 1fr;
            margin-top: 20px;
          }
          .docs-left-sidebar {
            display: none;
          }
        }
      `}</style>
    </>
  );
}
