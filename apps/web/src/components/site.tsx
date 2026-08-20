"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { AboutMenu } from "@/components/about-menu";
import { CookieControls } from "@/components/cookie-controls";
import { FlatIcon } from "@/components/flat-icons";
import { CivicUser, getSession, onAuthStateChange } from "@/lib/auth";

const productLinks: Array<[string, string]> = [
  ["Workspace", "/workspace"],
  ["Docs", "/docs"],
];

const docsNavTabs: Array<{ label: string; href: string; slug: string; icon: string }> = [
  { label: "Overview", href: "/docs", slug: "", icon: "overview" },
  { label: "System Architecture", href: "/docs/architecture", slug: "architecture", icon: "architecture" },
  { label: "Operations & Workflow", href: "/docs/workflow", slug: "workflow", icon: "workflow" },
  { label: "Governance & Safety", href: "/docs/safety", slug: "safety", icon: "shield" },
  { label: "API Reference", href: "/docs/api", slug: "api", icon: "api" },
];

const aboutLinks: Array<[string, string]> = [
  ["Explore Civitas", "/about/app"],
  ["Why It Is Needed", "/about/why"],
  ["Engineering Team", "/about/developers"],
];

function Wordmark() {
  return (
    <Link className="brand" href="/" aria-label="Civitas home">
      <span className="brand-mark" aria-hidden="true">
        <i />
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
  const [currentUser, setCurrentUser] = useState<CivicUser | null>(() => getSession()?.user || null);

  useEffect(() => {
    const unsubscribe = onAuthStateChange((user) => {
      setCurrentUser(user);
    });
    return () => {
      unsubscribe();
    };
  }, []);

  const isLinkActive = (href: string) => {
    if (href === "/") return pathname === "/";
    if (href === "/profile") return pathname.startsWith("/profile");
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
              className={`button small report-cta-btn ${isReportActive ? "active-button" : ""}`}
              href="/report"
            >
              Report an issue
            </Link>

            {/* SIGN IN / PROFILE BUTTON AT FAR RIGHT */}
            {currentUser && !pathname.startsWith("/sign-in") ? (
              <Link
                href="/profile"
                className={`nav-user-pill ${pathname.startsWith("/profile") ? "active" : ""}`}
                title={`Signed in as ${currentUser.name}`}
              >
                <span className="user-avatar-dot">
                  {currentUser.name.slice(0, 2).toUpperCase()}
                </span>
                <span className="user-nav-name">{currentUser.name.split(" ")[0]}</span>
              </Link>
            ) : (
              <Link
                href="/sign-in"
                className={`outline small sign-in-btn ${pathname.startsWith("/sign-in") ? "active" : ""}`}
              >
                Sign In
              </Link>
            )}

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
                <Link href="/profile" className={pathname.startsWith("/profile") ? "active" : ""}>
                  Resident Profile
                </Link>
                <Link href="/sign-in" className={pathname.startsWith("/sign-in") ? "active" : ""}>
                  Sign In / Switch Persona
                </Link>
              </div>
            </details>
          </div>
        </nav>
      </header>
      {docs && <DocsSubNav />}

      <style jsx>{`
        .nav-end {
          display: flex;
          align-items: center;
          gap: 10px;
        }
        .report-cta-btn {
          white-space: nowrap;
        }
        .sign-in-btn {
          padding: 7px 14px;
          font-size: 0.78rem;
          font-weight: 800;
          border: 1px solid #172019;
          background: #ffffff;
          color: #172019;
          border-radius: 4px;
          text-decoration: none;
          transition: all 0.15s ease;
          box-shadow: 2px 2px 0 #172019;
          white-space: nowrap;
        }
        .sign-in-btn:hover,
        .sign-in-btn.active {
          background: #172019;
          color: #ffffff;
        }
        .nav-user-pill {
          display: inline-flex;
          align-items: center;
          gap: 8px;
          padding: 4px 10px;
          border: 1px solid #172019;
          background: #fbf9f4;
          border-radius: 20px;
          text-decoration: none;
          color: #172019;
          font-size: 0.75rem;
          font-weight: 800;
          box-shadow: 2px 2px 0 #172019;
          transition: all 0.15s ease;
        }
        .nav-user-pill:hover,
        .nav-user-pill.active {
          background: #172019;
          color: #ffffff;
        }
        .user-avatar-dot {
          width: 22px;
          height: 22px;
          border-radius: 50%;
          background: #0f5f4f;
          color: #ffffff;
          display: grid;
          place-items: center;
          font-size: 0.65rem;
          font-weight: 900;
        }
      `}</style>
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
                <FlatIcon name={tab.icon} size={14} />
                <span>{tab.label}</span>
              </Link>
            );
          })}
        </div>

        <div className="docs-subnav-right">
          <div className="docs-search-wrapper">
            <FlatIcon name="search" size={14} color="#687067" />
            <input
              type="text"
              placeholder="Filter topics & schemas..."
              value={searchTerm}
              onChange={(e) => handleSearch(e.target.value)}
              className="docs-search-input"
              aria-label="Filter documentation"
            />
          </div>
          <span className="docs-version-pill">v0.1.0 · LangGraph</span>
        </div>
      </div>

      <style jsx>{`
        .docs-subnav-ribbon {
          border-bottom: 1px solid #172019;
          background: #ffffff;
          position: sticky;
          top: 74px;
          z-index: 40;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
        }
        .docs-subnav-inner {
          width: min(calc(100% - 40px), 1280px);
          margin: 0 auto;
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 8px 0;
          gap: 16px;
          flex-wrap: wrap;
        }
        .docs-nav-tabs {
          display: flex;
          align-items: center;
          gap: 8px;
          overflow-x: auto;
          padding: 2px 0;
        }
        .docs-tab-link {
          display: inline-flex;
          align-items: center;
          gap: 7px;
          padding: 7px 14px;
          border: 1px solid #e2ded4;
          background: #fbf9f4;
          border-radius: 4px;
          font-size: 0.78rem;
          font-weight: 750;
          color: #555e54;
          text-decoration: none;
          white-space: nowrap;
          transition: all 0.15s ease;
        }
        .docs-tab-link:hover {
          border-color: #172019;
          color: #172019;
          background: #ffffff;
        }
        .docs-tab-link.active {
          border-color: #172019;
          background: #172019;
          color: #ffffff;
          box-shadow: 2px 2px 0 #0f5f4f;
        }
        .docs-subnav-right {
          display: flex;
          align-items: center;
          gap: 12px;
        }
        .docs-search-wrapper {
          display: flex;
          align-items: center;
          gap: 8px;
          background: #fbf9f4;
          border: 1px solid #172019;
          padding: 5px 10px;
          border-radius: 4px;
        }
        .docs-search-input {
          border: 0;
          background: transparent;
          font-size: 0.76rem;
          outline: none;
          font-family: inherit;
          width: 170px;
          color: #172019;
        }
        .docs-version-pill {
          padding: 4px 8px;
          border: 1px solid #0f5f4f;
          background: #dce8dd;
          color: #0f5f4f;
          font-size: 0.64rem;
          font-weight: 850;
          border-radius: 4px;
          letter-spacing: 0.05em;
          white-space: nowrap;
        }
        @media (max-width: 960px) {
          .docs-subnav-inner {
            flex-direction: column;
            align-items: stretch;
            gap: 10px;
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
        {/* BRAND & MISSION */}
        <div className="footer-col brand-col">
          <Wordmark />
          <p className="footer-tagline">
            Evidence-backed civic incident intelligence with human oversight and transparent PostGIS clustering.
          </p>
          <div className="footer-status-pill">
            <span className="live-dot" />
            <span>OPERATIONAL · POSTGIS ENABLED</span>
          </div>
        </div>

        {/* PRODUCT */}
        <div className="footer-col">
          <span className="footer-heading">PRODUCT</span>
          <Link href="/workspace">Command Center</Link>
          <Link href="/report">Submit Citizen Report</Link>
          <Link href="/docs">System Docs</Link>
          <Link href="/docs/api">REST API Explorer</Link>
        </div>

        {/* GOVERNANCE */}
        <div className="footer-col">
          <span className="footer-heading">GOVERNANCE</span>
          <Link href="/about/app">Explore Civitas</Link>
          <Link href="/docs/architecture">Architecture</Link>
          <Link href="/privacy">Privacy & Geolocation</Link>
          <Link href="/terms">Terms of Service</Link>
        </div>

        {/* ACCOUNT */}
        <div className="footer-col">
          <span className="footer-heading">ACCOUNT</span>
          <Link href="/profile">Resident Profile</Link>
          <Link href="/sign-in">Sign In / Switch Persona</Link>
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
        .live-dot {
          width: 7px;
          height: 7px;
          border-radius: 50%;
          background: #0f5f4f;
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

export function SectionLabel({
  index = "01",
  children,
}: {
  index?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="section-label">
      <span>{index}</span>
      <p>{children}</p>
    </div>
  );
}

export function Status({
  tone = "neutral",
  children,
}: {
  tone?: "neutral" | "good" | "warn" | "danger";
  children: React.ReactNode;
}) {
  const formatLabel = (val: string) => {
    switch (val.toUpperCase()) {
      case "WAITING_FOR_REVIEW":
      case "WAITING FOR REVIEW":
        return "Review Required";
      case "WAITING_FOR_CLARIFICATION":
      case "WAITING FOR CLARIFICATION":
        return "Clarification";
      case "ASSIGNED":
        return "Assigned";
      case "RESOLVED":
        return "Resolved";
      case "IN_PROGRESS":
      case "IN PROGRESS":
        return "In Progress";
      case "SIGNED_OUT_PREVIEW":
      case "SIGNED OUT PREVIEW":
        return "Signed Out Preview";
      default:
        return val.replaceAll("_", " ");
    }
  };

  const label = typeof children === "string" ? formatLabel(children) : children;

  return (
    <span className={`status-pill-badge tone-${tone}`}>
      <span className="status-badge-dot" />
      <span className="status-badge-text">{label}</span>
    </span>
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
  return (
    <>
      <Nav />
      <main className="docs-dual-layout">
        {/* LEFT TOPIC SIDEBAR WITH FLAT ICONS */}
        <aside className="docs-left-sidebar" aria-label="Documentation topics">
          <div className="sidebar-group">
            <span className="sidebar-group-title">GETTING STARTED</span>
            <Link href="/docs" className={activeSlug === "" ? "active" : ""}>
              <FlatIcon name="overview" size={14} />
              <span>System Overview</span>
            </Link>
            <Link href="/docs/architecture" className={activeSlug === "architecture" ? "active" : ""}>
              <FlatIcon name="architecture" size={14} />
              <span>System Architecture</span>
            </Link>
          </div>

          <div className="sidebar-group">
            <span className="sidebar-group-title">OPERATIONS & AI</span>
            <Link href="/docs/workflow" className={activeSlug === "workflow" ? "active" : ""}>
              <FlatIcon name="workflow" size={14} />
              <span>Workflow & Operations</span>
            </Link>
            <Link href="/docs/lifecycle" className={activeSlug === "lifecycle" ? "active" : ""}>
              <FlatIcon name="overview" size={14} />
              <span>End-to-End Lifecycle</span>
            </Link>
            <Link href="/docs/safety" className={activeSlug === "safety" ? "active" : ""}>
              <FlatIcon name="shield" size={14} />
              <span>Governance & Safety</span>
            </Link>
          </div>

          <div className="sidebar-group">
            <span className="sidebar-group-title">INTEGRATION</span>
            <Link href="/docs/api" className={activeSlug === "api" ? "active" : ""}>
              <FlatIcon name="api" size={14} />
              <span>REST API Reference</span>
            </Link>
          </div>
        </aside>

        {/* CENTER MAIN ARTICLE */}
        <article className="docs-article-body">
          <div className="docs-article-header">
            <span className="docs-breadcrumb">
              CIVITAS DOCUMENTATION / {activeSlug ? activeSlug.toUpperCase() : "OVERVIEW"}
            </span>
            <h1 className="docs-article-title">{title}</h1>
            {intro && <p className="docs-article-intro">{intro}</p>}
          </div>

          {children}
        </article>

        {/* RIGHT ON-THIS-PAGE TOC */}
        {tocItems && tocItems.length > 0 && (
          <aside className="docs-right-toc" aria-label="Table of contents">
            <div className="toc-sticky-box">
              <span className="toc-title">ON THIS PAGE</span>
              <nav className="toc-nav">
                {tocItems.map((item) => (
                  <a key={item.id} href={`#${item.id}`}>
                    {item.label}
                  </a>
                ))}
              </nav>
            </div>
          </aside>
        )}
      </main>
      <Footer />

      <style jsx>{`
        .docs-dual-layout {
          width: min(calc(100% - 40px), 1360px);
          margin: 35px auto 100px;
          display: grid;
          grid-template-columns: 240px minmax(0, 1fr) 220px;
          gap: 40px;
          align-items: start;
        }
        .docs-left-sidebar {
          position: sticky;
          top: 90px;
          display: flex;
          flex-direction: column;
          gap: 24px;
        }
        .sidebar-group {
          display: flex;
          flex-direction: column;
          gap: 4px;
        }
        .sidebar-group-title {
          font-size: 0.62rem;
          font-weight: 900;
          letter-spacing: 0.12em;
          color: #0f5f4f;
          margin-bottom: 6px;
          padding-left: 8px;
        }
        .sidebar-group :global(a) {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 8px 12px;
          font-size: 0.82rem;
          font-weight: 700;
          color: #555e54;
          text-decoration: none;
          border-radius: 4px;
          transition: all 0.15s ease;
        }
        .sidebar-group :global(a:hover) {
          background: #fbf9f4;
          color: #172019;
        }
        .sidebar-group :global(a.active) {
          background: #172019;
          color: #ffffff;
          box-shadow: 2px 2px 0 #0f5f4f;
        }
        .docs-article-body {
          min-width: 0;
        }
        .docs-article-header {
          padding-bottom: 24px;
          border-bottom: 1px solid #172019;
          margin-bottom: 32px;
        }
        .docs-breadcrumb {
          font-size: 0.65rem;
          font-weight: 900;
          letter-spacing: 0.12em;
          color: #0f5f4f;
          display: block;
          margin-bottom: 8px;
        }
        .docs-article-title {
          font-size: clamp(2.4rem, 4vw, 3.8rem);
          font-family: Georgia, serif;
          margin: 0 0 14px;
          color: #172019;
          line-height: 1;
        }
        .docs-article-intro {
          font-size: 1.05rem;
          color: #555e54;
          line-height: 1.6;
          margin: 0;
        }
        .docs-right-toc {
          position: sticky;
          top: 90px;
        }
        .toc-sticky-box {
          border-left: 2px solid #e2ded4;
          padding-left: 16px;
        }
        .toc-title {
          font-size: 0.62rem;
          font-weight: 900;
          letter-spacing: 0.12em;
          color: #687067;
          display: block;
          margin-bottom: 10px;
        }
        .toc-nav {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }
        .toc-nav a {
          font-size: 0.78rem;
          color: #555e54;
          text-decoration: none;
          line-height: 1.4;
          transition: color 0.15s ease;
        }
        .toc-nav a:hover {
          color: #e84d7a;
        }
        @media (max-width: 1100px) {
          .docs-dual-layout {
            grid-template-columns: 220px 1fr;
          }
          .docs-right-toc {
            display: none;
          }
        }
        @media (max-width: 800px) {
          .docs-dual-layout {
            grid-template-columns: 1fr;
          }
          .docs-left-sidebar {
            position: static;
            flex-direction: row;
            overflow-x: auto;
            border-bottom: 1px solid #e2ded4;
            padding-bottom: 16px;
          }
          .sidebar-group {
            flex-direction: row;
          }
        }
      `}</style>
    </>
  );
}
