import Link from "next/link";

export function Nav({ docs = false }: { docs?: boolean }) {
  const links: Array<[string, string]> = docs
    ? [["Overview", "/docs"], ["Architecture", "/docs/architecture"], ["Workflow", "/docs/workflow"], ["Agents", "/docs/agents"], ["ML", "/docs/ml"], ["Knowledge", "/docs/knowledge"], ["API", "/docs/api"], ["Evaluation", "/docs/evaluation"], ["Safety", "/docs/safety"], ["Deployment", "/docs/deployment"]]
    : [["Product", "/workspace"], ["Demo workflow", "/demo-workflow"], ["Docs", "/docs"], ["Profile", "/profile"]];
  const aboutLinks = !docs && <><Link href="/about/app">About App</Link><Link href="/about/why">Why It Is Needed</Link><Link href="/about/developers">About Developers</Link></>;

  return <nav className={docs ? "docsnav" : "nav"} aria-label={docs ? "Documentation navigation" : "Primary navigation"}><Link className="brand" href="/">Civitas</Link><div className="navlinks">{links.map(([label, href]) => <Link key={href} href={href}>{label}</Link>)}{aboutLinks && <details className="aboutmenu"><summary>About</summary><div>{aboutLinks}</div></details>}</div><details className="mobilemenu"><summary>Menu</summary><div>{links.map(([label, href]) => <Link key={href} href={href}>{label}</Link>)}{aboutLinks}</div></details>{!docs && <Link className="button small" href="/report">Report an issue</Link>}</nav>;
}

export function Status({ children }: { children: string }) {
  return <span className="status">{children.replaceAll("_", " ").toLowerCase()}</span>;
}

export function DocsPage({ title, children }: { title: string; children: React.ReactNode }) {
  return <><Nav docs /><main className="docs"><aside>Documentation<br /><small>Evidence-backed operations</small></aside><article><p className="eyebrow">Civitas documentation</p><h1>{title}</h1>{children}</article></main></>;
}
