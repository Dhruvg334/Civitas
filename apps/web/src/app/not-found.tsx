import Link from "next/link";
import { Nav, Footer } from "@/components/site";

export default function NotFound() {
  return (
    <>
      <Nav />
      <main style={{ minHeight: "70vh", display: "flex", alignItems: "center", justifyContent: "center", padding: "2rem" }}>
        <div style={{ textAlign: "center", maxWidth: "480px" }}>
          <span style={{ fontSize: "3.5rem", fontWeight: "800", background: "linear-gradient(135deg, #6366f1, #3b82f6)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent", display: "block" }}>
            404
          </span>
          <h1 style={{ fontSize: "1.75rem", fontWeight: "700", margin: "0.5rem 0", color: "#f8fafc" }}>
            Incident Context Not Found
          </h1>
          <p style={{ color: "#94a3b8", fontSize: "0.9375rem", marginBottom: "1.75rem", lineHeight: "1.6" }}>
            The requested incident record, trace, or page does not exist or has been archived.
          </p>
          <Link
            href="/workspace"
            style={{ display: "inline-block", padding: "0.75rem 1.5rem", background: "linear-gradient(135deg, #2563eb, #1d4ed8)", color: "#ffffff", borderRadius: "8px", textDecoration: "none", fontWeight: "600" }}
          >
            Go to Operational Workspace
          </Link>
        </div>
      </main>
      <Footer />
    </>
  );
}
