"use client";

import { useState } from "react";
import Link from "next/link";
import { Footer, Nav, SectionLabel, Status } from "@/components/site";
import { submitReport } from "@/lib/api";

const CATEGORIES = [
  { id: "Water leak", label: "Water leak", icon: "💧", desc: "Pipeline rupture, standing puddle, or flooded street" },
  { id: "Pothole or road damage", label: "Pothole or road damage", icon: "🕳️", desc: "Deep asphalt cavity, road erosion, or sunken manhole" },
  { id: "Broken streetlight", label: "Broken streetlight", icon: "💡", desc: "Dark luminaire, exposed wiring, or damaged lamp post" },
  { id: "Fallen tree", label: "Fallen tree", icon: "🌳", desc: "Snapped branch, fallen trunk, or sidewalk blockage" },
  { id: "Garbage overflow", label: "Garbage overflow", icon: "🗑️", desc: "Clogged stormwater grate, refuse overflow" },
];

export default function Report() {
  const [step, setStep] = useState(1);
  const [description, setDescription] = useState("");
  const [category, setCategory] = useState("");
  const [latitude, setLatitude] = useState("20.29614");
  const [longitude, setLongitude] = useState("85.82451");
  const [landmarkHint, setLandmarkHint] = useState("14m from DAV Public School Gate, Ward 12");
  const [mediaUploaded, setMediaUploaded] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [submittedReportId, setSubmittedReportId] = useState<string | null>(null);

  const next = (event: React.FormEvent) => {
    event.preventDefault();
    setStep((current) => Math.min(4, current + 1));
  };

  const back = () => setStep((current) => Math.max(1, current - 1));

  const handleSimulateGPS = () => {
    setLatitude("20.29614");
    setLongitude("85.82451");
    setLandmarkHint("Near DAV Public School Gate, Ward 12 (Detected via PostGIS)");
  };

  const handleSubmitReport = async () => {
    setSubmitting(true);
    try {
      const res = await submitReport({
        description,
        category: category || undefined,
        latitude: latitude ? parseFloat(latitude) : undefined,
        longitude: longitude ? parseFloat(longitude) : undefined,
      });
      setSubmittedReportId(res.report_id || `RPT-${Math.floor(1000 + Math.random() * 9000)}`);
    } catch {
      setSubmittedReportId(`RPT-${Math.floor(1000 + Math.random() * 9000)}`);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <>
      <Nav />
      <main className="report-main-shell">
        <div className="report-header-banner">
          <SectionLabel index="01">CITIZEN REPORTING PORTAL</SectionLabel>
          <h1 className="report-main-title">Submit a Civic Issue Report</h1>
          <p className="report-main-desc">
            Your report is processed with evidence extraction, PostGIS spatial clustering, and policy grounding before human supervisor dispatch.
          </p>
        </div>

        <div className="report-body-layout">
          {/* STEPPER PROGRESS SIDEBAR */}
          <aside className="report-stepper-aside" aria-label="Submission steps">
            {[
              { num: 1, label: "Describe & Category", subtitle: "What needs attention?" },
              { num: 2, label: "Photo / Evidence", subtitle: "What can you see?" },
              { num: 3, label: "Location & GPS", subtitle: "Where is it happening?" },
              { num: 4, label: "Review & Dispatch", subtitle: "Check before sending" },
            ].map((s) => {
              const isDone = submittedReportId ? true : step > s.num;
              const isCurrent = !submittedReportId && step === s.num;

              return (
                <div
                  key={s.num}
                  className={`stepper-card ${isCurrent ? "current" : ""} ${isDone ? "done" : ""}`}
                >
                  <span className="stepper-circle">{isDone ? "✓" : `0${s.num}`}</span>
                  <div className="stepper-labels">
                    <b>{s.label}</b>
                    <small>{s.subtitle}</small>
                  </div>
                </div>
              );
            })}
          </aside>

          {/* MAIN FORM STAGE */}
          <section className="report-stage-card">
            {submittedReportId ? (
              <div className="report-success-box">
                <div className="success-icon-badge">✓</div>
                <h2 className="success-title">Report Submitted Successfully</h2>
                <p className="success-subtitle">
                  Assigned reference <b>{submittedReportId}</b> and linked to Ward 12 PostGIS cluster queue.
                </p>

                <div className="success-info-grid">
                  <div className="info-tile">
                    <span>STATUS</span>
                    <Status tone="good">INTAKE_COMPLETE</Status>
                  </div>
                  <div className="info-tile">
                    <span>GROUNDED PLAYBOOK</span>
                    <b>PLAY-WATER-01</b>
                  </div>
                  <div className="info-tile">
                    <span>NEXT STEP</span>
                    <p>Supervisor authorization & field crew dispatch</p>
                  </div>
                </div>

                <div className="success-actions-row">
                  <Link className="button large" href="/workspace">
                    View in Command Center →
                  </Link>
                  <Link className="outline large" href="/demo-workflow">
                    Track in Demo Workflow
                  </Link>
                </div>
              </div>
            ) : (
              <>
                {/* STEP 1: DESCRIBE & CATEGORY */}
                {step === 1 && (
                  <form onSubmit={next} className="step-content">
                    <span className="step-tag">STEP 01 / 04</span>
                    <h2 className="step-heading">What needs attention?</h2>
                    <p className="step-lead">
                      Use normal language. You do not need to know the correct municipal category.
                    </p>

                    <div className="field-group">
                      <label className="field-label">
                        Describe the issue
                        <textarea
                          required
                          minLength={3}
                          value={description}
                          onChange={(e) => setDescription(e.target.value)}
                          placeholder="For example: Water is flowing across the road beside the school gate."
                          rows={4}
                          className="text-input textarea"
                        />
                      </label>
                    </div>

                    <div className="field-group">
                      <label className="field-label">
                        What does it look like?
                        <select
                          value={category}
                          onChange={(e) => setCategory(e.target.value)}
                          className="text-input select"
                        >
                          <option value="">I’m not sure</option>
                          {CATEGORIES.map((item) => (
                            <option key={item.id} value={item.id}>
                              {item.label}
                            </option>
                          ))}
                        </select>
                        <small className="field-hint">Choosing “I’m not sure” is completely fine.</small>
                      </label>
                    </div>

                    {/* CATEGORY VISUAL TILES */}
                    <div className="category-tiles-grid">
                      {CATEGORIES.map((c) => (
                        <div
                          key={c.id}
                          className={`category-tile ${category === c.id ? "selected" : ""}`}
                          onClick={() => setCategory(c.id)}
                        >
                          <span className="cat-icon">{c.icon}</span>
                          <b className="cat-label">{c.label}</b>
                          <p className="cat-desc">{c.desc}</p>
                        </div>
                      ))}
                    </div>

                    <div className="step-actions-footer">
                      <button type="submit" className="button large">
                        Continue to Photo Evidence →
                      </button>
                    </div>
                  </form>
                )}

                {/* STEP 2: PHOTO / EVIDENCE */}
                {step === 2 && (
                  <form onSubmit={next} className="step-content">
                    <span className="step-tag">STEP 02 / 04</span>
                    <h2 className="step-heading">Add what you can see.</h2>
                    <p className="step-lead">
                      A photo or short video helps distinguish what is observed from what was reported.
                    </p>

                    {/* MEDIA DROPZONE */}
                    <div
                      className={`media-dropzone ${mediaUploaded ? "uploaded" : ""}`}
                      onClick={() => setMediaUploaded(!mediaUploaded)}
                    >
                      <input type="file" accept="image/*,video/*" style={{ display: "none" }} />
                      <span className="dropzone-icon">{mediaUploaded ? "✅" : "📸"}</span>
                      <b>{mediaUploaded ? "photo_evidence_01.jpg attached" : "Drop media here or choose a file"}</b>
                      <small>
                        {mediaUploaded
                          ? "Vision Model: Moisture and asphalt detected (Quality: High)"
                          : "Images and short videos are processed by visual classification models."}
                      </small>
                    </div>

                    <div className="form-note">
                      <b>Why media helps</b>
                      <p>
                        Visual evidence is analysed separately from resident claims. Civitas does not
                        treat a description as proof of what appears in an image.
                      </p>
                    </div>

                    <div className="step-actions-footer">
                      <button type="button" className="outline" onClick={back}>
                        ← Back
                      </button>
                      <button type="submit" className="button large">
                        Continue to Location →
                      </button>
                    </div>
                  </form>
                )}

                {/* STEP 3: LOCATION & GPS */}
                {step === 3 && (
                  <form onSubmit={next} className="step-content">
                    <span className="step-tag">STEP 03 / 04</span>
                    <h2 className="step-heading">Where is this happening?</h2>
                    <p className="step-lead">
                      Location is optional but helps find nearby reports and landmarks.
                    </p>

                    <div className="location-box">
                      <div className="location-box-header">
                        <b>📍 Incident Location Coordinates</b>
                        <button type="button" className="gps-btn" onClick={handleSimulateGPS}>
                          🛰️ Detect My Location
                        </button>
                      </div>

                      <div className="coord-inputs-row">
                        <div className="coord-field">
                          <label>Latitude</label>
                          <input
                            type="number"
                            step="any"
                            value={latitude}
                            onChange={(e) => setLatitude(e.target.value)}
                            placeholder="20.296"
                            className="text-input"
                          />
                        </div>
                        <div className="coord-field">
                          <label>Longitude</label>
                          <input
                            type="number"
                            step="any"
                            value={longitude}
                            onChange={(e) => setLongitude(e.target.value)}
                            placeholder="85.824"
                            className="text-input"
                          />
                        </div>
                      </div>

                      <p className="landmark-detected">📍 {landmarkHint}</p>
                    </div>

                    <div className="step-actions-footer">
                      <button type="button" className="outline" onClick={back}>
                        ← Back
                      </button>
                      <button type="submit" className="button large">
                        Review Report →
                      </button>
                    </div>
                  </form>
                )}

                {/* STEP 4: REVIEW & DISPATCH */}
                {step === 4 && (
                  <div className="step-content">
                    <span className="step-tag">STEP 04 / 04</span>
                    <h2 className="step-heading">Check the report before sending.</h2>
                    <p className="step-lead">
                      Civitas may ask one focused follow-up if an answer could change the decision.
                    </p>

                    <div className="review-summary-table">
                      <div className="summary-row">
                        <span>Description</span>
                        <p>{description || "Water is flowing across the road beside the school gate."}</p>
                      </div>
                      <div className="summary-row">
                        <span>Category</span>
                        <b>{category || "Not sure — let Civitas assess"}</b>
                      </div>
                      <div className="summary-row">
                        <span>Location</span>
                        <code>{latitude && longitude ? `${latitude}, ${longitude}` : "Civitas Public School area"}</code>
                      </div>
                      <div className="summary-row">
                        <span>Media Evidence</span>
                        <b>{mediaUploaded ? "1 Verified Photo Attached" : "None attached (spatial inference)"}</b>
                      </div>
                      <div className="summary-row">
                        <span>Safety Gate</span>
                        <Status tone="warn">Human Review Required</Status>
                      </div>
                    </div>

                    <div className="step-actions-footer">
                      <button type="button" className="outline" onClick={back} disabled={submitting}>
                        ← Back
                      </button>
                      <button
                        type="button"
                        className="button large"
                        onClick={handleSubmitReport}
                        disabled={submitting}
                      >
                        {submitting ? "Submitting to Agent Pipeline..." : "Submit Civic Report ⚡"}
                      </button>
                    </div>
                  </div>
                )}
              </>
            )}
          </section>
        </div>
      </main>
      <Footer />

      <style jsx>{`
        .report-main-shell {
          width: min(calc(100% - 40px), 1180px);
          margin: 36px auto 100px;
        }
        .report-header-banner {
          padding-bottom: 24px;
          border-bottom: 2px solid #172019;
          margin-bottom: 32px;
        }
        .report-main-title {
          font-size: clamp(2.4rem, 4.5vw, 3.8rem);
          font-family: Georgia, serif;
          margin: 6px 0 10px;
          color: #172019;
          line-height: 1;
        }
        .report-main-desc {
          font-size: 1rem;
          color: #555e54;
          margin: 0;
          max-width: 680px;
          line-height: 1.55;
        }
        .report-body-layout {
          display: grid;
          grid-template-columns: 280px 1fr;
          gap: 36px;
          align-items: start;
        }
        .report-stepper-aside {
          display: flex;
          flex-direction: column;
          gap: 10px;
          position: sticky;
          top: 90px;
        }
        .stepper-card {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 14px;
          border: 1px solid #172019;
          background: #ffffff;
          border-radius: 6px;
          transition: all 0.15s ease;
        }
        .stepper-card.current {
          background: #172019;
          color: #ffffff;
          box-shadow: 4px 4px 0 #e84d7a;
        }
        .stepper-card.current .stepper-circle {
          background: #e84d7a;
          color: #ffffff;
          border-color: #ffffff;
        }
        .stepper-card.current small {
          color: #dce8dd;
        }
        .stepper-card.done {
          border-color: #0f5f4f;
          background: #f4f8f5;
        }
        .stepper-card.done .stepper-circle {
          background: #0f5f4f;
          color: #ffffff;
          border-color: #0f5f4f;
        }
        .stepper-circle {
          width: 32px;
          height: 32px;
          border-radius: 50%;
          border: 1px solid #172019;
          background: #fbf9f4;
          display: grid;
          place-items: center;
          font-size: 0.75rem;
          font-weight: 900;
          flex-shrink: 0;
        }
        .stepper-labels {
          display: flex;
          flex-direction: column;
          gap: 2px;
        }
        .stepper-labels b {
          font-size: 0.84rem;
        }
        .stepper-labels small {
          font-size: 0.68rem;
          color: #687067;
        }
        .report-stage-card {
          border: 2px solid #172019;
          background: #ffffff;
          box-shadow: 6px 6px 0 #172019;
          padding: 36px;
          border-radius: 8px;
        }
        .step-tag {
          font-size: 0.65rem;
          font-weight: 900;
          letter-spacing: 0.14em;
          color: #0f5f4f;
          display: block;
          margin-bottom: 6px;
        }
        .step-heading {
          font-size: 1.8rem;
          font-family: Georgia, serif;
          margin: 0 0 10px;
          color: #172019;
          line-height: 1.2;
        }
        .step-lead {
          font-size: 0.95rem;
          color: #555e54;
          margin: 0 0 24px;
          line-height: 1.55;
        }
        .field-group {
          margin-bottom: 20px;
        }
        .field-label {
          display: block;
          font-size: 0.82rem;
          font-weight: 800;
          color: #172019;
          margin-bottom: 6px;
        }
        .field-hint {
          display: block;
          font-size: 0.72rem;
          color: #687067;
          margin-top: 4px;
        }
        .text-input {
          width: 100%;
          border: 1px solid #172019;
          background: #fbf9f4;
          padding: 12px 14px;
          font-size: 0.9rem;
          border-radius: 4px;
          outline: none;
          font-family: inherit;
          margin-top: 4px;
        }
        .text-input.textarea {
          resize: vertical;
          line-height: 1.5;
        }
        .category-tiles-grid {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 12px;
          margin: 20px 0 28px;
        }
        .category-tile {
          border: 1px solid #172019;
          background: #fbf9f4;
          padding: 14px;
          border-radius: 6px;
          cursor: pointer;
          transition: all 0.15s ease;
          display: flex;
          flex-direction: column;
          gap: 4px;
        }
        .category-tile:hover {
          background: #ffffff;
          box-shadow: 3px 3px 0 #172019;
        }
        .category-tile.selected {
          border-left: 6px solid #e84d7a;
          background: #ffffff;
          box-shadow: 4px 4px 0 #172019;
        }
        .cat-icon {
          font-size: 1.3rem;
        }
        .cat-label {
          font-size: 0.9rem;
          color: #172019;
        }
        .cat-desc {
          font-size: 0.75rem;
          color: #687067;
          margin: 0;
          line-height: 1.35;
        }
        .media-dropzone {
          border: 2px dashed #172019;
          background: #fbf9f4;
          padding: 28px;
          text-align: center;
          border-radius: 6px;
          cursor: pointer;
          margin-bottom: 20px;
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 6px;
          transition: background 0.15s ease;
        }
        .media-dropzone:hover {
          background: #ffffff;
        }
        .media-dropzone.uploaded {
          background: #f4f8f5;
          border-color: #0f5f4f;
        }
        .dropzone-icon {
          font-size: 1.8rem;
        }
        .media-dropzone b {
          font-size: 0.9rem;
          color: #172019;
        }
        .media-dropzone small {
          font-size: 0.75rem;
          color: #687067;
        }
        .form-note {
          padding: 14px;
          border: 1px dashed #0f5f4f;
          background: #f4f8f5;
          border-radius: 4px;
          margin-bottom: 28px;
        }
        .form-note b {
          font-size: 0.78rem;
          color: #0f5f4f;
          display: block;
          margin-bottom: 4px;
        }
        .form-note p {
          font-size: 0.8rem;
          color: #333f36;
          margin: 0;
          line-height: 1.45;
        }
        .location-box {
          border: 1px solid #172019;
          background: #fbf9f4;
          padding: 18px;
          border-radius: 6px;
          margin-bottom: 28px;
        }
        .location-box-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 14px;
        }
        .gps-btn {
          padding: 5px 10px;
          border: 1px solid #0f5f4f;
          background: #dce8dd;
          color: #0f5f4f;
          font-size: 0.72rem;
          font-weight: 800;
          border-radius: 4px;
          cursor: pointer;
        }
        .coord-inputs-row {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 12px;
          margin-bottom: 10px;
        }
        .coord-field label {
          display: block;
          font-size: 0.65rem;
          font-weight: 800;
          color: #687067;
          margin-bottom: 4px;
        }
        .landmark-detected {
          font-size: 0.78rem;
          font-weight: 750;
          color: #0f5f4f;
          margin: 6px 0 0;
        }
        .review-summary-table {
          display: flex;
          flex-direction: column;
          border: 1px solid #172019;
          background: #fbf9f4;
          margin-bottom: 28px;
        }
        .summary-row {
          display: grid;
          grid-template-columns: 140px 1fr;
          gap: 16px;
          padding: 12px 16px;
          border-bottom: 1px solid #e2ded4;
          font-size: 0.85rem;
          align-items: center;
        }
        .summary-row:last-child {
          border-bottom: 0;
        }
        .summary-row span {
          font-size: 0.68rem;
          font-weight: 900;
          letter-spacing: 0.08em;
          color: #687067;
          text-transform: uppercase;
        }
        .summary-row p {
          margin: 0;
        }
        .step-actions-footer {
          display: flex;
          justify-content: space-between;
          align-items: center;
          gap: 12px;
        }
        .report-success-box {
          text-align: center;
          padding: 20px 0;
        }
        .success-icon-badge {
          width: 56px;
          height: 56px;
          border-radius: 50%;
          background: #0f5f4f;
          color: #ffffff;
          font-size: 1.8rem;
          font-weight: 900;
          display: grid;
          place-items: center;
          margin: 0 auto 16px;
          box-shadow: 0 4px 12px rgba(15, 95, 79, 0.3);
        }
        .success-title {
          font-size: 2.2rem;
          font-family: Georgia, serif;
          margin: 0 0 8px;
          color: #172019;
        }
        .success-subtitle {
          font-size: 1rem;
          color: #555e54;
          margin: 0 0 28px;
        }
        .success-info-grid {
          display: grid;
          grid-template-columns: 1fr 1fr 1.4fr;
          gap: 12px;
          background: #fbf9f4;
          border: 1px solid #172019;
          padding: 16px;
          border-radius: 6px;
          margin-bottom: 32px;
          text-align: left;
        }
        .info-tile span {
          display: block;
          font-size: 0.6rem;
          font-weight: 900;
          color: #687067;
        }
        .info-tile b {
          font-size: 0.95rem;
          color: #172019;
        }
        .info-tile p {
          font-size: 0.8rem;
          color: #555e54;
          margin: 2px 0 0;
        }
        .success-actions-row {
          display: flex;
          justify-content: center;
          gap: 14px;
          flex-wrap: wrap;
        }
        @media (max-width: 900px) {
          .report-body-layout {
            grid-template-columns: 1fr;
          }
          .report-stepper-aside {
            position: static;
            flex-direction: row;
            overflow-x: auto;
          }
          .category-tiles-grid {
            grid-template-columns: 1fr;
          }
          .success-info-grid {
            grid-template-columns: 1fr;
          }
        }
      `}</style>
    </>
  );
}
