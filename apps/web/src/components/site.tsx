import Link from "next/link";

import { CookieControls } from "@/components/cookie-controls";

const productLinks: Array<[string, string]> = [["Workspace", "/workspace"], ["Demo", "/demo-workflow"], ["Docs", "/docs"], ["Profile", "/profile"]];
const docsLinks: Array<[string, string]> = [["Overview", "/docs"], ["System", "/docs/architecture"], ["Operations", "/docs/workflow"], ["Governance", "/docs/safety"], ["API", "/docs/api"]];
const aboutLinks: Array<[string, string]> = [["About App", "/about/app"], ["Why It Is Needed", "/about/why"], ["Team behind", "/about/developers"]];

function Wordmark() {
  return <Link className="brand" href="/" aria-label="Civitas home"><span className="brand-mark" aria-hidden="true"><i /><i /><i /></span><span>Civitas</span></Link>;
}

export function Nav({ docs = false }: { docs?: boolean }) {
  const links = docs ? docsLinks : productLinks;
  return <header className={docs ? "docs-shell-nav" : "site-header"}><nav className={docs ? "docsnav" : "nav"} aria-label={docs ? "Documentation navigation" : "Primary navigation"}><Wordmark /><div className="nav-center">{links.map(([label, href]) => <Link key={href} href={href}>{label}</Link>)}{!docs && <details className="aboutmenu"><summary>About</summary><div className="about-popover"><p className="popover-kicker">Explore Civitas</p>{aboutLinks.map(([label, href]) => <Link key={href} href={href}>{label}</Link>)}</div></details>}</div><div className="nav-end">{docs ? <Link className="nav-back" href="/">Back to product</Link> : <Link className="button small" href="/report">Report an issue</Link>}<details className="mobilemenu"><summary aria-label="Open navigation"><span /><span /></summary><div>{links.map(([label, href]) => <Link key={href} href={href}>{label}</Link>)}{!docs && aboutLinks.map(([label, href]) => <Link key={href} href={href}>{label}</Link>)}{docs && <Link href="/">Back to product</Link>}</div></details></div></nav></header>;
}

export function Footer() {
  return <footer className="footer"><div><Link className="brand footer-brand" href="/"><span className="brand-mark" aria-hidden="true"><i /><i /><i /></span><span>Civitas</span></Link><p>Evidence-backed civic intelligence with people in the loop.</p></div><div className="footer-links"><Link href="/docs">System docs</Link><Link href="/about/app">About Civitas</Link><Link href="/privacy">Privacy & location</Link><Link href="/terms">Terms of use</Link></div><CookieControls /></footer>;
}

export function Status({ children, tone = "neutral" }: { children: string; tone?: "neutral" | "good" | "warn" | "danger" }) {
  return <span className={`status status-${tone}`}><i aria-hidden="true" />{children.replaceAll("_", " ").toLowerCase()}</span>;
}

export function SectionLabel({ index, children }: { index?: string; children: React.ReactNode }) {
  return <div className="section-label">{index && <span>{index}</span>}<p>{children}</p></div>;
}

export function DocsPage({ title, intro, children }: { title: string; intro?: string; children: React.ReactNode }) {
  return <><Nav docs /><main className="docs-layout"><article className="docs-article"><div className="docs-heading"><span className="doc-number">CIVITAS / DOCS</span><h1>{title}</h1>{intro && <p>{intro}</p>}</div>{children}</article></main><Footer /></>;
}
