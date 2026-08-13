"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { AboutMenu } from "@/components/about-menu";
import { CookieControls } from "@/components/cookie-controls";

const productLinks: Array<[string, string]> = [
  ["Workspace", "/workspace"],
  ["Demo", "/demo-workflow"],
  ["Docs", "/docs"],
  ["Profile", "/profile"],
];

const docsLinks: Array<[string, string]> = [
  ["Overview", "/docs"],
  ["System", "/docs/architecture"],
  ["Operations", "/docs/workflow"],
  ["Governance", "/docs/safety"],
  ["API", "/docs/api"],
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

export function Nav({ docs = false }: { docs?: boolean }) {
  const pathname = usePathname() || "";
  const links = docs ? docsLinks : productLinks;

  const isLinkActive = (href: string) => {
    if (href === "/") return pathname === "/";
    if (href === "/profile") return pathname.startsWith("/profile") || pathname.startsWith("/sign-in");
    if (href === "/workspace") return pathname.startsWith("/workspace") || pathname.startsWith("/incidents");
    return pathname.startsWith(href);
  };

  const isAboutActive = pathname.startsWith("/about");
  const isReportActive = pathname.startsWith("/report");

  return (
    <header className={docs ? "docs-shell-nav" : "site-header"}>
      <nav
        className={docs ? "docsnav" : "nav"}
        aria-label={docs ? "Documentation navigation" : "Primary navigation"}
      >
        <Wordmark />
        <div className="nav-center">
          {links.map(([label, href]) => {
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
          {!docs && <AboutMenu isActive={isAboutActive} />}
        </div>
        <div className="nav-end">
          {docs ? (
            <Link className="nav-back" href="/">
              Back to product
            </Link>
          ) : (
            <Link
              className={`button small ${isReportActive ? "active-button" : ""}`}
              href="/report"
            >
              Report an issue
            </Link>
          )}
          <details className="mobilemenu">
            <summary aria-label="Open navigation">
              <span />
              <span />
            </summary>
            <div>
              {links.map(([label, href]) => (
                <Link
                  key={href}
                  href={href}
                  className={isLinkActive(href) ? "active" : ""}
                >
                  {label}
                </Link>
              ))}
              {!docs &&
                aboutLinks.map(([label, href]) => (
                  <Link
                    key={href}
                    href={href}
                    className={pathname.startsWith(href) ? "active" : ""}
                  >
                    {label}
                  </Link>
                ))}
              {docs && <Link href="/">Back to product</Link>}
            </div>
          </details>
        </div>
      </nav>
    </header>
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
  children,
}: {
  title: string;
  intro?: string;
  children: React.ReactNode;
}) {
  return (
    <>
      <Nav docs />
      <main className="docs-layout">
        <article className="docs-article">
          <div className="docs-heading">
            <span className="doc-number">CIVITAS / DOCS</span>
            <h1>{title}</h1>
            {intro && <p>{intro}</p>}
          </div>
          {children}
        </article>
      </main>
      <Footer />
    </>
  );
}
