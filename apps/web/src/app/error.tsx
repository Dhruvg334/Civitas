"use client";

import { useEffect } from "react";
import Link from "next/link";
import { FlatIcon } from "@/components/flat-icons";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("Next.js app route error:", error);
  }, [error]);

  return (
    <main style={{ minHeight: "80vh", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", padding: "2rem", textAlign: "center" }}>
      <div style={{ background: "rgba(18, 24, 38, 0.8)", border: "1px solid rgba(239, 68, 68, 0.3)", padding: "2.5rem", borderRadius: "16px", maxWidth: "500px", display: "flex", flexDirection: "column", alignItems: "center" }}>
        <div style={{ marginBottom: "1rem" }}>
          <FlatIcon name="alert" size={38} color="#f87171" />
        </div>
        <h1 style={{ fontSize: "1.5rem", fontWeight: "700", color: "#f87171", marginBottom: "0.5rem" }}>
          Unexpected Application Error
        </h1>
        <p style={{ color: "#94a3b8", fontSize: "0.9375rem", marginBottom: "1.5rem", lineHeight: "1.5" }}>
          Civitas encountered an issue processing this view. No operational data was modified.
        </p>
        <div style={{ display: "flex", gap: "1rem", justifyContent: "center" }}>
          <button
            onClick={() => reset()}
            style={{ padding: "0.625rem 1.25rem", background: "#3b82f6", color: "#ffffff", border: "none", borderRadius: "8px", fontWeight: "600", cursor: "pointer" }}
          >
            Try Again
          </button>
          <Link
            href="/workspace"
            style={{ padding: "0.625rem 1.25rem", background: "rgba(255,255,255,0.05)", color: "#cbd5e1", border: "1px solid rgba(255,255,255,0.1)", borderRadius: "8px", textDecoration: "none", fontWeight: "500" }}
          >
            Return to Command Center
          </Link>
        </div>
      </div>
    </main>
  );
}
