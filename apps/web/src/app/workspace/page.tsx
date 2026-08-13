import Link from "next/link";
import { MiniMap } from "@/components/civic-visuals";
import { Nav, Status } from "@/components/site";

const rows = [
  { id: "INC-0241", title: "Water leak near school crossing", category: "Water leakage", priority: "High", reports: 3, department: "Water + Traffic", status: "WAITING_FOR_REVIEW", tone: "warn" as const },
  { id: "INC-0240", title: "Blocked pedestrian pathway", category: "Fallen tree", priority: "Medium", reports: 2, department: "Public Works", status: "RUNNING", tone: "neutral" as const },
  { id: "INC-0238", title: "Streetlight outage on ward road", category: "Streetlight", priority: "High", reports: 1, department: "Electrical", status: "WAITING_FOR_CLARIFICATION", tone: "neutral" as const },
];

export default function Workspace() {
  return <><Nav /><main className="workspace-shell">
    <header className="workspace-header"><div><span className="workspace-kicker">MUNICIPAL OPERATIONS / DEMO DATA</span><h1>Incident command</h1><p>Prioritized incidents, spatial context and workflow state in one operating view.</p></div><div className="workspace-actions"><button className="outline">Filters <span>3</span></button><button className="button">Queue settings</button></div></header>
    <section className="ops-strip" aria-label="Queue summary"><div><span>Open incidents</span><b>03</b><small>seeded workspace</small></div><div><span>Awaiting review</span><b>01</b><small>human action needed</small></div><div><span>Clarification</span><b>01</b><small>resident response needed</small></div><div><span>Highest priority</span><b>P1</b><small>school crossing leak</small></div></section>
    <div className="workspace-grid"><section className="queue-panel"><div className="panel-heading"><div><span>INCIDENT QUEUE</span><h2>Needs attention</h2></div><button className="icon-button" aria-label="More queue options">•••</button></div><div className="queue-list">{rows.map((row, index) => <Link className={`incident-row ${index === 0 ? "selected" : ""}`} href="/incidents/demo-water" key={row.id}><span className="row-index">{String(index + 1).padStart(2, "0")}</span><div className="incident-main"><span>{row.id} · {row.category}</span><b>{row.title}</b><small>{row.department} · {row.reports} report{row.reports > 1 ? "s" : ""}</small></div><div className="incident-priority"><span>Priority</span><b>{row.priority}</b></div><Status tone={row.tone}>{row.status}</Status></Link>)}</div></section>
    <section className="map-panel"><div className="panel-heading"><div><span>SPATIAL CONTEXT</span><h2>Ward 12 overview</h2></div><span className="live-dot">Seeded</span></div><MiniMap /><div className="map-context"><div><span>Selected</span><b>INC-0241</b></div><div><span>Nearby landmark</span><b>Govt. School · 42 m</b></div><div><span>Related reports</span><b>3 within candidate window</b></div></div></section></div>
  </main></>;
}
