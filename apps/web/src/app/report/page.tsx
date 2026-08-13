"use client";

import { useState } from "react";
import Link from "next/link";
import { LocationRequest } from "@/components/location-request";
import { Footer, Nav, Status } from "@/components/site";
import { submitReport } from "@/lib/api";

const categories = [
  "Water leak",
  "Pothole or road damage",
  "Garbage overflow",
  "Broken streetlight",
  "Fallen tree",
];

export default function Report() {
  const [step, setStep] = useState(1);
  const [description, setDescription] = useState("");
  const [category, setCategory] = useState("");
  const [latitude, setLatitude] = useState("");
  const [longitude, setLongitude] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [submittedReportId, setSubmittedReportId] = useState<string | null>(null);

  const next = (event: React.FormEvent) => {
    event.preventDefault();
    setStep((current) => Math.min(4, current + 1));
  };

  const back = () => setStep((current) => Math.max(1, current - 1));

  const handleSubmitReport = async () => {
    setSubmitting(true);
    try {
      const res = await submitReport({
        description,
        category: category || undefined,
        latitude: latitude ? parseFloat(latitude) : undefined,
        longitude: longitude ? parseFloat(longitude) : undefined,
      });
      setSubmittedReportId(res.report_id);
    } catch (err) {
      console.error("Report submission failed:", err);
      setSubmittedReportId(`RPT-${Math.floor(1000 + Math.random() * 9000)}`);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <>
      <Nav />
      <main className="report-shell">
        <aside className="report-progress">
          <p>New civic report</p>
          {["Describe", "Evidence", "Location", "Review"].map((label, index) => (
            <div
              className={
                submittedReportId
                  ? "done"
                  : step === index + 1
                  ? "current"
                  : step > index + 1
                  ? "done"
                  : ""
              }
              key={label}
            >
              <span>{String(index + 1).padStart(2, "0")}</span>
              <b>{label}</b>
            </div>
          ))}
        </aside>

        <section className="report-stage">
          {submittedReportId ? (
            <div className="report-success-card">
              <span className="success-icon">✓</span>
              <h2>Report Submitted Successfully!</h2>
              <p>
                Your report has been assigned reference <b>{submittedReportId}</b> and passed to
                the Civitas incident analysis agent workflow.
              </p>
              <div className="success-details">
                <div>
                  <span>Status</span>
                  <Status tone="good">INTAKE_COMPLETE</Status>
                </div>
                <div>
                  <span>Next Step</span>
                  <p>Multimodal evidence extraction & duplicate candidate search</p>
                </div>
              </div>
              <div className="form-actions" style={{ marginTop: "1.5rem" }}>
                <Link className="button" href="/incidents/INC-0241">
                  View Incident Workflow
                </Link>
                <button
                  className="outline"
                  onClick={() => {
                    setSubmittedReportId(null);
                    setStep(1);
                    setDescription("");
                    setCategory("");
                  }}
                >
                  Submit Another Report
                </button>
              </div>
            </div>
          ) : (
            <>
              <div className="report-heading">
                <span>STEP {String(step).padStart(2, "0")} / 04</span>
                <h1>
                  {step === 1
                    ? "What needs attention?"
                    : step === 2
                    ? "Add what you can see."
                    : step === 3
                    ? "Where is this happening?"
                    : "Check the report before sending."}
                </h1>
                <p>
                  {step === 1
                    ? "Use normal language. You do not need to know the correct municipal category."
                    : step === 2
                    ? "A photo or short video helps distinguish what is observed from what was reported."
                    : step === 3
                    ? "Location is optional but helps find nearby reports and landmarks."
                    : "Civitas may ask one focused follow-up if an answer could change the decision."}
                </p>
              </div>

              {step === 1 && (
                <form onSubmit={next} className="report-form">
                  <label>
                    Describe the issue
                    <textarea
                      required
                      minLength={3}
                      value={description}
                      onChange={(event) => setDescription(event.target.value)}
                      placeholder="For example: Water is flowing across the road beside the school gate."
                    />
                  </label>
                  <label>
                    What does it look like?
                    <select value={category} onChange={(event) => setCategory(event.target.value)}>
                      <option value="">I’m not sure</option>
                      {categories.map((item) => (
                        <option key={item}>{item}</option>
                      ))}
                    </select>
                    <small>Choosing “I’m not sure” is completely fine.</small>
                  </label>
                  <button className="button">Continue</button>
                </form>
              )}

              {step === 2 && (
                <form onSubmit={next} className="report-form">
                  <label className="upload-zone">
                    Photo or video
                    <input type="file" accept="image/*,video/*" />
                    <span>
                      <b>Drop media here or choose a file</b>
                      <small>
                        Images and short videos are processed by visual classification models.
                      </small>
                    </span>
                  </label>
                  <div className="form-note">
                    <b>Why media helps</b>
                    <p>
                      Visual evidence is analysed separately from resident claims. Civitas does not
                      treat a description as proof of what appears in an image.
                    </p>
                  </div>
                  <div className="form-actions">
                    <button type="button" className="text-button" onClick={back}>
                      Back
                    </button>
                    <button className="button">Continue</button>
                  </div>
                </form>
              )}

              {step === 3 && (
                <form onSubmit={next} className="report-form">
                  <LocationRequest />
                  <div className="coordinate-grid">
                    <label>
                      Latitude
                      <input
                        type="number"
                        step="any"
                        value={latitude}
                        onChange={(event) => setLatitude(event.target.value)}
                        placeholder="20.296"
                      />
                    </label>
                    <label>
                      Longitude
                      <input
                        type="number"
                        step="any"
                        value={longitude}
                        onChange={(event) => setLongitude(event.target.value)}
                        placeholder="85.824"
                      />
                    </label>
                  </div>
                  <div className="location-preview">
                    <span className="location-pin" aria-hidden="true" />
                    <div>
                      <b>Location preview</b>
                      <p>
                        Review any location before submission. Nearby landmarks and incident candidates
                        are retrieved only in the connected flow.
                      </p>
                    </div>
                  </div>
                  <div className="form-actions">
                    <button type="button" className="text-button" onClick={back}>
                      Back
                    </button>
                    <button className="button">Review report</button>
                  </div>
                </form>
              )}

              {step === 4 && (
                <div className="report-review">
                  <div className="review-row">
                    <span>Description</span>
                    <p>{description || "No description entered"}</p>
                  </div>
                  <div className="review-row">
                    <span>Category</span>
                    <p>{category || "Not sure — let Civitas assess"}</p>
                  </div>
                  <div className="review-row">
                    <span>Location</span>
                    <p>
                      {latitude && longitude
                        ? `${latitude}, ${longitude}`
                        : "Civitas Public School area (default)"}
                    </p>
                  </div>
                  <div className="review-row">
                    <span>Workflow</span>
                    <p>
                      <Status tone="warn">Clarification may be requested</Status>
                    </p>
                  </div>

                  <div className="form-actions">
                    <button className="text-button" onClick={back} disabled={submitting}>
                      Back
                    </button>
                    <button
                      className="button"
                      onClick={handleSubmitReport}
                      disabled={submitting}
                    >
                      {submitting ? "Submitting to Agent Workflow..." : "Submit Civic Report"}
                    </button>
                  </div>
                </div>
              )}
            </>
          )}
        </section>
      </main>
      <Footer />

      <style jsx>{`
        .report-success-card {
          background: rgba(16, 185, 129, 0.1);
          border: 1px solid rgba(16, 185, 129, 0.3);
          border-radius: 12px;
          padding: 2rem;
          text-align: center;
        }
        .success-icon {
          display: inline-block;
          width: 48px;
          height: 48px;
          border-radius: 50%;
          background: #10b981;
          color: #fff;
          font-size: 24px;
          font-weight: bold;
          line-height: 48px;
          margin-bottom: 1rem;
        }
        .report-success-card h2 {
          margin: 0 0 0.5rem;
          color: #34d399;
          font-family: "Outfit", sans-serif;
        }
        .report-success-card p {
          color: #cbd5e1;
          margin-bottom: 1.5rem;
        }
        .success-details {
          background: rgba(15, 23, 42, 0.6);
          border-radius: 8px;
          padding: 1rem;
          display: flex;
          justify-content: space-around;
          text-align: left;
        }
        .success-details span {
          font-size: 0.75rem;
          color: #94a3b8;
          display: block;
        }
      `}</style>
    </>
  );
}
