"use client";

import Link from "next/link";
import { Nav, Footer } from "@/components/site";

export default function NotFound() {
  return (
    <>
      <Nav />
      <main className="not-found-main">
        <div className="not-found-card">
          <span className="not-found-code">404</span>
          <h1 className="not-found-title">Page or Dossier Not Found</h1>
          <p className="not-found-lead">
            The requested incident record, documentation slug, or workflow trace does not exist or has been relocated.
          </p>
          <div className="not-found-actions">
            <Link href="/workspace" className="button large">
              Go to Command Center →
            </Link>
            <Link href="/" className="outline large">
              Return Home
            </Link>
          </div>
        </div>
      </main>
      <Footer />

      <style jsx>{`
        .not-found-main {
          min-height: 65vh;
          display: grid;
          place-items: center;
          padding: 60px 20px;
        }
        .not-found-card {
          max-width: 540px;
          text-align: center;
          padding: 40px;
          border: 2px solid #172019;
          background: #ffffff;
          box-shadow: 6px 6px 0 #172019;
          border-radius: 8px;
        }
        .not-found-code {
          font-size: 3.8rem;
          font-weight: 900;
          color: #e84d7a;
          line-height: 1;
          display: block;
          margin-bottom: 8px;
          font-family: Georgia, serif;
        }
        .not-found-title {
          font-size: 2rem;
          font-family: Georgia, serif;
          margin: 0 0 12px;
          color: #172019;
        }
        .not-found-lead {
          color: #555e54;
          font-size: 0.95rem;
          line-height: 1.6;
          margin: 0 0 28px;
        }
        .not-found-actions {
          display: flex;
          justify-content: center;
          gap: 12px;
          flex-wrap: wrap;
        }
      `}</style>
    </>
  );
}
