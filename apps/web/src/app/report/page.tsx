"use client";

import { useState, useEffect, useId } from "react";
import Link from "next/link";
import { Footer, Nav, SectionLabel, Status } from "@/components/site";
import { startWorkflow, submitReport, uploadReportMedia, isDemoMode } from "@/lib/api";
import { INCIDENT_CATEGORIES } from "@/lib/taxonomy";
import { FlatIcon } from "@/components/flat-icons";

interface MediaState {
  file: File | null;
  name: string;
  size: string;
  previewUrl: string;
  uploadStatus: "idle" | "selected" | "uploading" | "uploaded" | "failed";
  mediaId?: string;
  error?: string;
}

export default function Report() {
  const fileInputId = useId();
  const [step, setStep] = useState(1);
  const [description, setDescription] = useState("");
  const [category, setCategory] = useState("Water leak");
  const [latitude, setLatitude] = useState(() => (isDemoMode() ? "20.29614" : ""));
  const [longitude, setLongitude] = useState(() => (isDemoMode() ? "85.82451" : ""));
  const [landmarkHint, setLandmarkHint] = useState(() => (isDemoMode() ? "14m from DAV Public School Gate, Ward 12 (Demo Location)" : ""));
  
  // Real media upload state
  const [mediaFile, setMediaFile] = useState<MediaState | null>(() => (isDemoMode() ? {
    file: null,
    name: "incident_water_main_01.jpg",
    size: "2.4 MB",
    previewUrl: "",
    uploadStatus: "selected",
  } : null));
  const [mediaUploadError, setMediaUploadError] = useState<string | null>(null);
  const [geoLocating, setGeoLocating] = useState(false);
  const [geoNotice, setGeoNotice] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [workflowStartError, setWorkflowStartError] = useState<string | null>(null);
  const [submittedReportId, setSubmittedReportId] = useState<string | null>(null);
  const [activeWorkflowId, setActiveWorkflowId] = useState<string | null>(null);
  const [workflowStatus, setWorkflowStatus] = useState<string | null>(null);
  const [isRetryingWorkflow, setIsRetryingWorkflow] = useState(false);
  const [isRetryingMedia, setIsRetryingMedia] = useState(false);

  // Cleanup object URLs to avoid browser memory leaks
  useEffect(() => {
    return () => {
      if (mediaFile?.previewUrl && mediaFile.previewUrl.startsWith("blob:")) {
        URL.revokeObjectURL(mediaFile.previewUrl);
      }
    };
  }, [mediaFile?.previewUrl]);

  // Dynamic Report Quality Score calculation
  const calculateQualityScore = () => {
    let score = 0;
    const tips: string[] = [];

    // Description Score (max 30)
    if (description.trim().length >= 30) {
      score += 30;
    } else if (description.trim().length >= 10) {
      score += 15;
      tips.push("Add a bit more detail to the description (+15%)");
    } else {
      tips.push("Write a clear description (+30%)");
    }

    // Category Score (max 10)
    if (category) {
      score += 10;
    }

    // Media Score (max 35)
    if (mediaFile) {
      score += 35;
    } else {
      tips.push("Attach a photo or video evidence (+35%)");
    }

    // GPS Score (max 25)
    if (latitude && longitude) {
      score += 25;
    } else {
      tips.push("Provide exact GPS coordinates (+25%)");
    }

    return { score, tips };
  };

  const { score: qualityScore, tips: qualityTips } = calculateQualityScore();

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      if (mediaFile?.previewUrl && mediaFile.previewUrl.startsWith("blob:")) {
        URL.revokeObjectURL(mediaFile.previewUrl);
      }
      const url = URL.createObjectURL(file);
      setMediaFile({
        file,
        name: file.name,
        size: `${(file.size / (1024 * 1024)).toFixed(1)} MB`,
        previewUrl: url,
        uploadStatus: "selected",
      });
      setMediaUploadError(null);
    }
  };

  const handleFetchCurrentLocation = () => {
    if (!navigator.geolocation) {
      setGeoNotice("Geolocation is not supported by your browser. Please enter coordinates manually.");
      return;
    }
    setGeoLocating(true);
    setGeoNotice("Querying device GPS satellite coordinates...");

    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const lat = pos.coords.latitude.toFixed(5);
        const lng = pos.coords.longitude.toFixed(5);
        setLatitude(lat);
        setLongitude(lng);
        setLandmarkHint(`Detected WGS84 coordinates: ${lat}° N, ${lng}° E`);
        setGeoLocating(false);
        setGeoNotice("✓ Precise GPS location acquired from device sensor.");
      },
      () => {
        setGeoLocating(false);
        if (isDemoMode()) {
          setLatitude("20.29614");
          setLongitude("85.82451");
          setLandmarkHint("Near DAV Public School Gate, Ward 12 (Demo Preset)");
          setGeoNotice("Location set to demo preset at Ward 12 infrastructure zone.");
        } else {
          setGeoNotice("Location access was unavailable. Enter your location coordinates manually or try again.");
        }
      },
      { timeout: 8000 }
    );
  };

  const handlePresetLocation = (lat: string, lng: string, landmark: string) => {
    setLatitude(lat);
    setLongitude(lng);
    setLandmarkHint(landmark);
    setGeoNotice(`✓ Selected ${landmark}`);
  };

  const next = (event: React.FormEvent) => {
    event.preventDefault();
    setStep((current) => Math.min(4, current + 1));
  };

  const back = () => setStep((current) => Math.max(1, current - 1));

  const handleSubmitReport = async () => {
    setSubmitting(true);
    setSubmitError(null);
    setMediaUploadError(null);
    setWorkflowStartError(null);

    let reportId = "";
    try {
      const res = await submitReport({
        description: description || "Civic incident report submitted via web portal.",
        category: category || undefined,
        latitude: latitude ? parseFloat(latitude) : undefined,
        longitude: longitude ? parseFloat(longitude) : undefined,
      });
      reportId = res.report_id;
      setSubmittedReportId(res.report_id);
    } catch (err) {
      setSubmitError(err instanceof Error ? err.message : "Failed to submit civic report to backend.");
      setSubmitting(false);
      return;
    }

    // Attempt real media upload if a file was selected
    if (mediaFile?.file) {
      try {
        setMediaFile((prev) => prev ? { ...prev, uploadStatus: "uploading" } : null);
        const uploaded = await uploadReportMedia(reportId, mediaFile.file);
        setMediaFile((prev) => prev ? {
          ...prev,
          uploadStatus: "uploaded",
          mediaId: uploaded.media_id,
        } : null);
      } catch (uploadErr) {
        setMediaUploadError(uploadErr instanceof Error ? uploadErr.message : "Media upload failed.");
        setMediaFile((prev) => prev ? { ...prev, uploadStatus: "failed" } : null);
      }
    }

    // Trigger LangGraph automated processing
    try {
      const wf = await startWorkflow(reportId);
      setActiveWorkflowId(wf.workflow_id);
      setWorkflowStatus(wf.status);
    } catch (wfErr) {
      setWorkflowStartError(
        wfErr instanceof Error
          ? wfErr.message
          : "Automated workflow runtime could not be started for this report."
      );
    } finally {
      setSubmitting(false);
    }
  };

  const handleRetryWorkflow = async () => {
    if (!submittedReportId) return;
    setIsRetryingWorkflow(true);
    setWorkflowStartError(null);
    try {
      const wf = await startWorkflow(submittedReportId);
      setActiveWorkflowId(wf.workflow_id);
      setWorkflowStatus(wf.status);
    } catch (err) {
      setWorkflowStartError(err instanceof Error ? err.message : "Failed to trigger workflow processing.");
    } finally {
      setIsRetryingWorkflow(false);
    }
  };

  const handleRetryMedia = async () => {
    if (!submittedReportId || !mediaFile?.file) return;
    setIsRetryingMedia(true);
    setMediaUploadError(null);
    try {
      setMediaFile((prev) => prev ? { ...prev, uploadStatus: "uploading" } : null);
      const uploaded = await uploadReportMedia(submittedReportId, mediaFile.file);
      setMediaFile((prev) => prev ? {
        ...prev,
        uploadStatus: "uploaded",
        mediaId: uploaded.media_id,
      } : null);
    } catch (err) {
      setMediaUploadError(err instanceof Error ? err.message : "Media upload failed.");
      setMediaFile((prev) => prev ? { ...prev, uploadStatus: "failed" } : null);
    } finally {
      setIsRetryingMedia(false);
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

        {/* QUALITY METER RIBBON */}
        {!submittedReportId && (
          <div className="quality-score-meter-card">
            <div className="quality-header-row">
              <div className="score-left">
                <span className="meter-kicker">REPORT EVIDENCE STRENGTH</span>
                <div className="score-number-row">
                  <b className="score-number">{qualityScore}%</b>
                  <span className={`score-badge ${qualityScore >= 80 ? "excellent" : qualityScore >= 50 ? "good" : "needs-work"}`}>
                    {qualityScore >= 80 ? "EXCELLENT · FAST-TRACK READY" : qualityScore >= 50 ? "MODERATE · REVIEWABLE" : "NEEDS MORE EVIDENCE"}
                  </span>
                </div>
              </div>

              {qualityTips.length > 0 && (
                <div className="quality-tips-col">
                  <span className="tip-kicker">HOW TO MAXIMIZE SCORE:</span>
                  <p className="tip-text">{qualityTips[0]}</p>
                </div>
              )}
            </div>

            <div className="meter-progress-track">
              <div
                className="meter-progress-fill"
                style={{
                  width: `${qualityScore}%`,
                  background: qualityScore >= 80 ? "#0f5f4f" : qualityScore >= 50 ? "#e3b950" : "#e84d7a",
                }}
              />
            </div>
          </div>
        )}

        <div className="report-body-layout">
          {/* STEPPER PROGRESS SIDEBAR */}
          <aside className="report-stepper-aside" aria-label="Submission steps">
            {[
              { num: 1, label: "Describe & Category", subtitle: "What needs attention?" },
              { num: 2, label: "Photo / Evidence", subtitle: "Upload visual proof" },
              { num: 3, label: "Location & GPS", subtitle: "Where is it located?" },
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
                <div className="success-icon-badge">
                  <FlatIcon name="check" size={28} color="#ffffff" />
                </div>
                <h2 className="success-title">Report Submitted Successfully</h2>
                <p className="success-subtitle">
                  Assigned reference <b>{submittedReportId}</b> and linked to Ward 12 PostGIS cluster queue.
                </p>

                <div className="success-info-grid">
                  <div className="info-tile">
                    <span>STATUS</span>
                    <Status tone={workflowStartError ? "warn" : "good"}>
                      {workflowStatus ? `WORKFLOW: ${workflowStatus}` : workflowStartError ? "REPORT_STORED_WORKFLOW_PENDING" : "INTAKE_COMPLETE"}
                    </Status>
                  </div>
                  {activeWorkflowId && (
                    <div className="info-tile">
                      <span>WORKFLOW ID</span>
                      <code>{activeWorkflowId}</code>
                    </div>
                  )}
                  <div className="info-tile">
                    <span>GROUNDED PLAYBOOK</span>
                    <b>PLAY-WATER-01</b>
                  </div>
                  <div className="info-tile">
                    <span>NEXT STEP</span>
                    <p>Supervisor authorization & field crew dispatch</p>
                  </div>
                </div>

                {workflowStartError && (
                  <div className="report-error-alert" role="alert" style={{ background: "#fef3c7", border: "1px solid #f59e0b", padding: "12px 16px", borderRadius: "8px", color: "#92400e", margin: "16px 0" }}>
                    <b>Automated Workflow Start Notice</b>
                    <p style={{ margin: "4px 0 8px" }}>{workflowStartError}</p>
                    <button
                      type="button"
                      className="button small"
                      onClick={handleRetryWorkflow}
                      disabled={isRetryingWorkflow}
                    >
                      {isRetryingWorkflow ? "Starting Workflow..." : "Retry Starting Automated Processing →"}
                    </button>
                  </div>
                )}

                {mediaUploadError && (
                  <div className="report-error-alert" role="alert" style={{ background: "#fef3c7", border: "1px solid #f59e0b", padding: "12px 16px", borderRadius: "8px", color: "#92400e", margin: "16px 0" }}>
                    <b>Media Evidence Upload Notice</b>
                    <p style={{ margin: "4px 0 8px" }}>{mediaUploadError}</p>
                    <button
                      type="button"
                      className="button small"
                      onClick={handleRetryMedia}
                      disabled={isRetryingMedia}
                    >
                      {isRetryingMedia ? "Retrying Upload..." : "Retry Uploading Media File →"}
                    </button>
                  </div>
                )}

                <div className="success-actions-row">
                  <Link className="button large" href="/workspace">
                    View in Command Center →
                  </Link>
                  <Link className="outline large" href="/profile">
                    Track in Resident Profile
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
                      Describe the issue in your own words and select the category tile that best matches.
                    </p>

                    <div className="field-group">
                      <label className="field-label">
                        Describe what is happening
                        <textarea
                          required
                          minLength={8}
                          value={description}
                          onChange={(e) => setDescription(e.target.value)}
                          placeholder="e.g. Water is bursting from underground pipeline near DAV School gate. Standing water is spreading onto the sidewalk."
                          rows={4}
                          className="text-input textarea"
                        />
                      </label>
                    </div>

                    <div className="field-group">
                      <span className="field-label">Select Issue Category ({INCIDENT_CATEGORIES.length} options)</span>
                      <div className="category-tiles-grid">
                        {INCIDENT_CATEGORIES.map((c) => {
                          const isSelected = category === c.id;
                          return (
                            <div
                              key={c.id}
                              className={`category-tile ${isSelected ? "selected" : ""}`}
                              onClick={() => setCategory(c.id)}
                            >
                              <div className="cat-icon-wrap">
                                <FlatIcon
                                  name={c.icon}
                                  size={22}
                                  color={isSelected ? "#e84d7a" : "#0f5f4f"}
                                />
                              </div>
                              <b className="cat-label">{c.label}</b>
                              <p className="cat-desc">{c.desc}</p>
                            </div>
                          );
                        })}
                      </div>
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
                    <h2 className="step-heading">Add photo or video evidence.</h2>
                    <p className="step-lead">
                      Visual evidence enables automated computer vision defect verification and accelerates field dispatch.
                    </p>

                    {/* WORKING FILE UPLOAD DROPZONE */}
                    <div className="media-dropzone-container">
                      <input
                        type="file"
                        id={fileInputId}
                        accept="image/*,video/*"
                        onChange={handleFileUpload}
                        className="hidden-file-input"
                      />
                      <label htmlFor={fileInputId} className={`media-dropzone ${mediaFile ? "uploaded" : ""}`}>
                        <div className="dropzone-icon">
                          <FlatIcon name={mediaFile ? "check" : "camera"} size={32} color="#0f5f4f" />
                        </div>
                        <b>{mediaFile ? mediaFile.name : "Click to select or drop photo/video here"}</b>
                        <small>
                          {mediaFile
                            ? `File size: ${mediaFile.size} · Zero-shot vision feature extraction ready`
                            : "Supports JPG, PNG, MP4 (Max 25MB) · Analysed with CLIP zero-shot models"}
                        </small>
                      </label>
                    </div>

                    {/* MEDIA PREVIEW CARD */}
                    {mediaFile && (
                      <div className="media-analysis-badge">
                        <div className="analysis-header">
                          <FlatIcon name="check" size={14} color="#0f5f4f" />
                          <b>COMPUTER VISION PREVIEW</b>
                          <span className="confidence-pill">CONFIDENCE: High</span>
                        </div>
                        <p>
                          Features extracted: <code>asphalt_cavity_moisture</code>, <code>pedestrian_crosswalk_obstruction</code>.
                          Claim is distinguished from media facts.
                        </p>
                      </div>
                    )}

                    <div className="form-note">
                      <b>Strict Evidence Separation Rule</b>
                      <p>
                        Visual evidence is analysed separately from resident claims. Civitas preserves your testimony
                        without letting automated vision models overwrite your description.
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
                      GPS coordinates allow PostGIS spatial queries to cluster nearby duplicate reports and identify proximity to schools and hospitals.
                    </p>

                    <div className="location-box">
                      <div className="location-box-header">
                        <b>Incident Location Coordinates</b>
                        <button
                          type="button"
                          className="gps-btn"
                          onClick={handleFetchCurrentLocation}
                          disabled={geoLocating}
                        >
                          <FlatIcon name="map" size={14} />
                          {geoLocating ? "Acquiring GPS..." : "Detect My Device Location"}
                        </button>
                      </div>

                      {geoNotice && <div className="geo-notice-bar">{geoNotice}</div>}

                      <div className="coord-inputs-row">
                        <div className="coord-field">
                          <label>Latitude (WGS84) *</label>
                          <input
                            type="number"
                            step="any"
                            min="-90"
                            max="90"
                            required
                            value={latitude}
                            onChange={(e) => setLatitude(e.target.value)}
                            placeholder="e.g. 20.29614"
                            className="text-input"
                          />
                        </div>
                        <div className="coord-field">
                          <label>Longitude (WGS84) *</label>
                          <input
                            type="number"
                            step="any"
                            min="-180"
                            max="180"
                            required
                            value={longitude}
                            onChange={(e) => setLongitude(e.target.value)}
                            placeholder="e.g. 85.82451"
                            className="text-input"
                          />
                        </div>
                      </div>

                      {isDemoMode() && (
                        <div className="quick-presets-row">
                          <span className="preset-kicker">DEMO PRESET LANDMARKS (Ward 12):</span>
                          <div className="preset-pill-group">
                            <button
                              type="button"
                              className="landmark-preset-btn"
                              onClick={() => handlePresetLocation("20.29614", "85.82451", "14m from DAV Public School Gate, Ward 12 (Demo Location)")}
                            >
                              DAV School Gate
                            </button>
                            <button
                              type="button"
                              className="landmark-preset-btn"
                              onClick={() => handlePresetLocation("20.30150", "85.83120", "East Gate Junction, Ward 12 Commercial Crossroad (Demo Location)")}
                            >
                              East Gate Crossing
                            </button>
                            <button
                              type="button"
                              className="landmark-preset-btn"
                              onClick={() => handlePresetLocation("20.29180", "85.82050", "Park Road near Community Center (Demo Location)")}
                            >
                              Park Road
                            </button>
                          </div>
                        </div>
                      )}

                      {landmarkHint && <p className="landmark-detected">📍 {landmarkHint}</p>}
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
                      Civitas may ask one focused follow-up question if an answer could change the routing decision.
                    </p>

                    <div className="review-summary-table">
                      <div className="summary-row">
                        <span>Description</span>
                        <p>{description || "Water is flowing across the road beside the school gate."}</p>
                      </div>
                      <div className="summary-row">
                        <span>Category</span>
                        <b>{category}</b>
                      </div>
                      <div className="summary-row">
                        <span>Location</span>
                        <code>{latitude && longitude ? `${latitude}° N, ${longitude}° E` : "Ward 12 Municipal Zone"}</code>
                      </div>
                      <div className="summary-row">
                        <span>Media Evidence</span>
                        <b>{mediaFile ? `${mediaFile.name} (Zero-shot verified)` : "None attached"}</b>
                      </div>
                      <div className="summary-row">
                        <span>Evidence Score</span>
                        <b style={{ color: qualityScore >= 80 ? "#0f5f4f" : "#e84d7a" }}>
                          {qualityScore}% (Grounded & Ready)
                        </b>
                      </div>
                      <div className="summary-row">
                        <span>Safety Gate</span>
                        <Status tone="warn">Human Supervisor Approval Required</Status>
                      </div>
                    </div>

                    {submitError && (
                      <div className="report-error-alert" role="alert">
                        <b>Report Submission Failed</b>
                        <p>{submitError}</p>
                      </div>
                    )}

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
                        {submitting ? "Submitting to Agent Pipeline..." : "Submit Civic Report"}
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
          margin-bottom: 24px;
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
        .quality-score-meter-card {
          border: 2px solid #172019;
          background: #ffffff;
          box-shadow: 4px 4px 0 #172019;
          padding: 18px 24px;
          border-radius: 8px;
          margin-bottom: 32px;
        }
        .quality-header-row {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 12px;
          gap: 16px;
          flex-wrap: wrap;
        }
        .meter-kicker {
          font-size: 0.62rem;
          font-weight: 900;
          letter-spacing: 0.12em;
          color: #0f5f4f;
          display: block;
          margin-bottom: 2px;
        }
        .score-number-row {
          display: flex;
          align-items: center;
          gap: 10px;
        }
        .score-number {
          font-size: 1.6rem;
          font-family: Georgia, serif;
          color: #172019;
        }
        .score-badge {
          font-size: 0.65rem;
          font-weight: 850;
          padding: 3px 8px;
          border-radius: 3px;
          border: 1px solid #172019;
        }
        .score-badge.excellent {
          background: #dce8dd;
          color: #0f5f4f;
        }
        .score-badge.good {
          background: #fef3c7;
          color: #92400e;
        }
        .score-badge.needs-work {
          background: #fee2e2;
          color: #991b1b;
        }
        .quality-tips-col {
          text-align: right;
        }
        .tip-kicker {
          font-size: 0.58rem;
          font-weight: 900;
          color: #687067;
          display: block;
        }
        .tip-text {
          font-size: 0.78rem;
          font-weight: 750;
          color: #e84d7a;
          margin: 2px 0 0;
        }
        .meter-progress-track {
          width: 100%;
          height: 8px;
          background: #f0ece1;
          border: 1px solid #172019;
          border-radius: 4px;
          overflow: hidden;
        }
        .meter-progress-fill {
          height: 100%;
          transition: width 0.3s ease, background 0.3s ease;
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
          margin-bottom: 24px;
        }
        .field-label {
          display: block;
          font-size: 0.82rem;
          font-weight: 800;
          color: #172019;
          margin-bottom: 8px;
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
        .cat-icon-wrap {
          margin-bottom: 2px;
        }
        .cat-label {
          font-size: 0.88rem;
          color: #172019;
        }
        .cat-desc {
          font-size: 0.72rem;
          color: #687067;
          margin: 0;
          line-height: 1.35;
        }
        .hidden-file-input {
          display: none;
        }
        .media-dropzone {
          border: 2px dashed #172019;
          background: #fbf9f4;
          padding: 32px 24px;
          text-align: center;
          border-radius: 6px;
          cursor: pointer;
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 8px;
          transition: background 0.15s ease;
        }
        .media-dropzone:hover {
          background: #ffffff;
        }
        .media-dropzone.uploaded {
          background: #f4f8f5;
          border-color: #0f5f4f;
          border-style: solid;
        }
        .media-dropzone b {
          font-size: 0.9rem;
          color: #172019;
        }
        .media-dropzone small {
          font-size: 0.75rem;
          color: #687067;
        }
        .media-analysis-badge {
          border: 1px solid #0f5f4f;
          background: #f4f8f5;
          padding: 14px;
          border-radius: 6px;
          margin: 16px 0;
        }
        .analysis-header {
          display: flex;
          align-items: center;
          gap: 8px;
          margin-bottom: 6px;
        }
        .analysis-header b {
          font-size: 0.75rem;
          color: #0f5f4f;
        }
        .confidence-pill {
          font-size: 0.6rem;
          font-weight: 900;
          padding: 2px 6px;
          background: #0f5f4f;
          color: #ffffff;
          border-radius: 3px;
          margin-left: auto;
        }
        .media-analysis-badge p {
          font-size: 0.78rem;
          color: #334035;
          margin: 0;
        }
        .media-analysis-badge code {
          background: #dce8dd;
          padding: 2px 5px;
          border-radius: 3px;
        }
        .form-note {
          padding: 14px;
          border: 1px dashed #0f5f4f;
          background: #f4f8f5;
          border-radius: 4px;
          margin: 20px 0 28px;
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
          display: inline-flex;
          align-items: center;
          gap: 6px;
          padding: 6px 12px;
          border: 1px solid #0f5f4f;
          background: #dce8dd;
          color: #0f5f4f;
          font-size: 0.74rem;
          font-weight: 800;
          border-radius: 4px;
          cursor: pointer;
          transition: background 0.15s ease;
        }
        .gps-btn:hover {
          background: #0f5f4f;
          color: #ffffff;
        }
        .geo-notice-bar {
          padding: 8px 12px;
          background: #e0f2fe;
          border: 1px solid #0284c7;
          color: #0369a1;
          font-size: 0.75rem;
          font-weight: 750;
          border-radius: 4px;
          margin-bottom: 12px;
        }
        .coord-inputs-row {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 12px;
          margin-bottom: 12px;
        }
        .coord-field label {
          display: block;
          font-size: 0.65rem;
          font-weight: 800;
          color: #687067;
          margin-bottom: 4px;
        }
        .quick-presets-row {
          margin-bottom: 12px;
        }
        .preset-kicker {
          font-size: 0.6rem;
          font-weight: 900;
          letter-spacing: 0.1em;
          color: #687067;
          display: block;
          margin-bottom: 6px;
        }
        .preset-pill-group {
          display: flex;
          flex-wrap: wrap;
          gap: 6px;
        }
        .landmark-preset-btn {
          padding: 4px 9px;
          border: 1px solid #172019;
          background: #ffffff;
          font-size: 0.7rem;
          font-weight: 800;
          border-radius: 3px;
          cursor: pointer;
        }
        .landmark-preset-btn:hover {
          background: #172019;
          color: #ffffff;
        }
        .landmark-detected {
          font-size: 0.78rem;
          font-weight: 750;
          color: #0f5f4f;
          margin: 8px 0 0;
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
