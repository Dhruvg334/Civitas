import Link from "next/link";

import { Footer, Nav } from "@/components/site";

const pages: Record<string, { title: string; intro: string; items: Array<[string, string]> }> = {
  history: { title: "Report history", intro: "A resident-facing timeline of reports and the incident state they became part of.", items: [["REPORT-103 · Today", "Water on road near school was grouped into INC-0241 and is waiting for municipal review."], ["REPORT-097 · 2 days ago", "Streetlight outage is awaiting a clarification response."], ["REPORT-088 · 6 days ago", "Blocked pedestrian path was sent to Public Works."]] },
  preferences: { title: "Preferences", intro: "Control the display name, area, communication channel and local preview storage associated with this device.", items: [["Display and area", "Choose how Civitas addresses you and the ward or neighbourhood used to make updates locally relevant."], ["Location", "Location permission is optional. You can decline it and use a landmark or coordinates for individual reports."], ["Cookie settings", "Essential storage supports local preview choices; optional cookies require an explicit choice."]] },
  security: { title: "Security & account", intro: "Authentication is not connected in this preview, so security actions remain intentionally non-destructive.", items: [["Password reset", "A production reset flow must verify the account email before issuing a reset link."], ["Municipal access", "Operational review is role-controlled and is never implied by a resident account."], ["Clear preview", "Local preview history may be cleared from the profile preferences section."]] },
};

export default async function ProfileSection({ params }: { params: Promise<{ section: string }> }) {
  const { section } = await params;
  const page = pages[section] ?? pages.preferences;
  return <><Nav /><main className="profile-subpage"><p className="section-kicker">Account / {section}</p><h1>{page.title}</h1><p className="legal-lede">{page.intro}</p><nav className="profile-subnav" aria-label="Profile sections"><Link href="/profile">Overview</Link><Link href="/profile/history">History</Link><Link href="/profile/preferences">Preferences</Link><Link href="/profile/security">Security</Link></nav><section className="detail-list">{page.items.map(([heading, body]) => <article key={heading}><h2>{heading}</h2><p>{body}</p></article>)}</section></main><Footer /></>;
}
