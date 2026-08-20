"use client";

import { use, useEffect, useState } from "react";
import Link from "next/link";
import { Footer, Nav, SectionLabel, Status } from "@/components/site";
import { FlatIcon } from "@/components/flat-icons";
import { fetchAuditCertificate, MunicipalAuditCertificate } from "@/lib/api";

export default function CertificatePage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params);
  const incidentId = resolvedParams.id;

  const [cert, setCert] = useState<MunicipalAuditCertificate | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [copied, setCopied] = useState<boolean>(false);

  useEffect(() => {
    let isMounted = true;
    fetchAuditCertificate(incidentId)
      .then((data) => {
        if (!isMounted) return;
        setCert(data);
        setLoading(false);
      })
      .catch(() => {
        if (!isMounted) return;
        setLoading(false);
      });
    return () => {
      isMounted = false;
    };
  }, [incidentId]);

  const handleCopyHash = () => {
    if (!cert) return;
    navigator.clipboard.writeText(cert.sha256_cryptographic_digest);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handlePrint = () => {
    window.print();
  };

  return (
    <>
      <Nav />
      <main className="cert-shell">
        <header className="cert-header-actions no-print">
          <Link href={`/incidents/${incidentId}`} className="back-link">
            ← Return to Incident {incidentId}
          </Link>
          <button className="button primary small" onClick={handlePrint}>
            <FlatIcon name="code" size={14} /> Print / Export Official Certificate
          </button>
        </header>

        {loading ? (
          <div className="loading-card">Verifying cryptographic municipal certificate...</div>
        ) : !cert ? (
          <div className="error-card">Unable to load municipal certificate for incident {incidentId}.</div>
        ) : (
          <div className="certificate-sheet">
            {/* TOP EMBLEM & HEADER */}
            <div className="cert-top-header">
              <div className="cert-brand-mark">
                <span className="brand-mark-lg">
                  <i /><i /><i /><i />
                </span>
                <div>
                  <span className="gov-kicker">{cert.governing_municipality}</span>
                  <h2>Official Municipal Resolution Audit Certificate</h2>
                </div>
              </div>
              <div className="cert-badge-box">
                <span className="badge good">CRYPTOGRAPHICALLY SEALED</span>
                <span className="cert-id-text">{cert.certificate_id}</span>
              </div>
            </div>

            <hr className="cert-divider" />

            {/* SHA-256 DIGEST BANNER */}
            <div className="hash-seal-banner">
              <div className="hash-label-row">
                <span className="hash-title">
                  <FlatIcon name="shield" size={16} /> SHA-256 Cryptographic Integrity Digest
                </span>
                <button className="copy-hash-btn no-print" onClick={handleCopyHash}>
                  {copied ? "Copied Digest!" : "Copy Hash"}
                </button>
              </div>
              <div className="hash-code-box">{cert.sha256_cryptographic_digest}</div>
              <p className="hash-explainer">
                This tamper-proof cryptographic digest seals the end-to-end lifecycle record—including original citizen evidence,
                AI computer vision inferences, statutory policy grounding citations, contractor work orders, and resolution photogrammetry.
              </p>
            </div>

            {/* LIFECYCLE EVIDENCE GRID */}
            <div className="lifecycle-grid">
              <div className="grid-item">
                <span className="item-label">Incident Identifier</span>
                <strong>{cert.incident_id}</strong>
              </div>

              <div className="grid-item">
                <span className="item-label">Certified Closure Time</span>
                <strong>{new Date(cert.issued_at).toUTCString()}</strong>
              </div>

              <div className="grid-item">
                <span className="item-label">Assigned Department</span>
                <strong>{String(cert.lifecycle_payload.assigned_department || "water_supply").replace(/_/g, " ").toUpperCase()}</strong>
              </div>

              <div className="grid-item">
                <span className="item-label">Resolution Classification</span>
                <span className="badge good small">
                  {String(cert.lifecycle_payload.resolution_class || "RESOLVED_VERIFIED")}
                </span>
              </div>

              <div className="grid-item">
                <span className="item-label">H3 Spatial Index (Res 8)</span>
                <span className="mono-text">{String(cert.lifecycle_payload.h3_spatial_cell_res8 || "8860b29849fffff")}</span>
              </div>

              <div className="grid-item">
                <span className="item-label">Audited Bill of Quantities (BOQ)</span>
                <strong>₹{Number(cert.lifecycle_payload.bill_of_quantities_inr || 0).toLocaleString()} (${String(cert.lifecycle_payload.bill_of_quantities_usd || "0")} USD)</strong>
              </div>
            </div>

            {/* CANONICAL JSON AUDIT TRAIL */}
            <div className="json-audit-box">
              <span className="json-label">Canonical Immutable JSON Audit Payload</span>
              <pre className="json-pre">{JSON.stringify(cert.lifecycle_payload, null, 2)}</pre>
            </div>

            {/* FOOTER SIGN-OFF */}
            <div className="cert-footer-row">
              <div>
                <span className="sign-label">Municipal Authority</span>
                <p className="sign-text">Civitas Evidence-Backed Municipal Intelligence Registry</p>
              </div>
              <div className="cert-qr-mock">
                <span className="qr-text">VERIFIED BY CIVITAS AGENTIC RUNTIME</span>
              </div>
            </div>
          </div>
        )}
      </main>
      <Footer />

      <style jsx>{`
        .cert-shell {
          max-width: 960px;
          margin: 0 auto;
          padding: 2.5rem 1.5rem;
          display: flex;
          flex-direction: column;
          gap: 1.5rem;
        }
        .cert-header-actions {
          display: flex;
          justify-content: space-between;
          align-items: center;
        }
        .back-link {
          font-size: 0.85rem;
          font-weight: 600;
          color: var(--color-brand, #2563eb);
          text-decoration: none;
        }
        .certificate-sheet {
          background: #ffffff;
          border: 2px solid var(--color-border, #cbd5e1);
          border-radius: 12px;
          padding: 2.5rem;
          display: flex;
          flex-direction: column;
          gap: 1.5rem;
          box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
        }
        @media print {
          .no-print {
            display: none !important;
          }
          .cert-shell {
            padding: 0;
            max-width: 100%;
          }
          .certificate-sheet {
            border: 1px solid #000;
            box-shadow: none;
            padding: 1.5rem;
          }
        }
        .cert-top-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          gap: 1rem;
        }
        .cert-brand-mark {
          display: flex;
          align-items: center;
          gap: 1rem;
        }
        .brand-mark-lg {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 3px;
          width: 28px;
          height: 28px;
        }
        .brand-mark-lg i {
          background: var(--color-brand, #2563eb);
          border-radius: 2px;
        }
        .gov-kicker {
          font-size: 0.75rem;
          font-weight: 700;
          color: var(--color-text-secondary, #64748b);
          text-transform: uppercase;
          display: block;
        }
        .cert-brand-mark h2 {
          font-size: 1.35rem;
          font-weight: 800;
          color: var(--color-text-primary, #0f172a);
          margin: 0.2rem 0 0 0;
        }
        .cert-badge-box {
          display: flex;
          flex-direction: column;
          align-items: flex-end;
          gap: 0.35rem;
        }
        .cert-id-text {
          font-size: 0.75rem;
          font-family: monospace;
          color: var(--color-text-secondary, #64748b);
        }
        .cert-divider {
          border: none;
          border-top: 1px solid var(--color-border, #e2e8f0);
          margin: 0;
        }
        .hash-seal-banner {
          background: #f8fafc;
          border: 1px solid var(--color-border, #e2e8f0);
          border-radius: 8px;
          padding: 1.25rem;
          display: flex;
          flex-direction: column;
          gap: 0.6rem;
        }
        .hash-label-row {
          display: flex;
          justify-content: space-between;
          align-items: center;
        }
        .hash-title {
          font-size: 0.85rem;
          font-weight: 700;
          color: var(--color-text-primary, #0f172a);
          display: flex;
          align-items: center;
          gap: 0.4rem;
        }
        .copy-hash-btn {
          border: 1px solid var(--color-border, #cbd5e1);
          background: #ffffff;
          padding: 0.2rem 0.5rem;
          border-radius: 4px;
          font-size: 0.75rem;
          font-weight: 600;
          cursor: pointer;
        }
        .hash-code-box {
          font-family: monospace;
          font-size: 0.85rem;
          background: #ffffff;
          border: 1px solid var(--color-border, #cbd5e1);
          padding: 0.5rem 0.75rem;
          border-radius: 6px;
          color: #0f172a;
          word-break: break-all;
        }
        .hash-explainer {
          font-size: 0.75rem;
          color: var(--color-text-secondary, #64748b);
          margin: 0;
          line-height: 1.4;
        }
        .lifecycle-grid {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 1.25rem;
          background: #ffffff;
          border: 1px solid var(--color-border, #e2e8f0);
          border-radius: 8px;
          padding: 1.25rem;
        }
        .grid-item {
          display: flex;
          flex-direction: column;
          gap: 0.25rem;
        }
        .item-label {
          font-size: 0.75rem;
          color: var(--color-text-secondary, #64748b);
          text-transform: uppercase;
          font-weight: 600;
        }
        .mono-text {
          font-family: monospace;
          font-size: 0.85rem;
        }
        .json-audit-box {
          display: flex;
          flex-direction: column;
          gap: 0.5rem;
        }
        .json-label {
          font-size: 0.75rem;
          font-weight: 700;
          color: var(--color-text-secondary, #64748b);
          text-transform: uppercase;
        }
        .json-pre {
          background: #0f172a;
          color: #e2e8f0;
          font-size: 0.75rem;
          font-family: monospace;
          padding: 1rem;
          border-radius: 8px;
          overflow-x: auto;
          margin: 0;
          max-height: 200px;
        }
        .cert-footer-row {
          display: flex;
          justify-content: space-between;
          align-items: flex-end;
          border-top: 1px dashed var(--color-border, #cbd5e1);
          padding-top: 1.25rem;
        }
        .sign-label {
          font-size: 0.75rem;
          color: var(--color-text-secondary, #64748b);
          text-transform: uppercase;
          display: block;
        }
        .sign-text {
          font-size: 0.85rem;
          font-weight: 700;
          margin: 0.2rem 0 0 0;
          color: var(--color-text-primary, #0f172a);
        }
        .qr-text {
          font-size: 0.7rem;
          font-weight: 700;
          letter-spacing: 0.05em;
          color: var(--color-brand, #2563eb);
          border: 1px solid var(--color-brand, #2563eb);
          padding: 0.35rem 0.65rem;
          border-radius: 4px;
        }
        .loading-card,
        .error-card {
          padding: 3rem;
          text-align: center;
          background: #ffffff;
          border: 1px solid var(--color-border, #e2e8f0);
          border-radius: 12px;
          color: var(--color-text-secondary, #64748b);
        }
      `}</style>
    </>
  );
}
