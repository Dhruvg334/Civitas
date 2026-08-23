"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { FlatIcon } from "@/components/flat-icons";
import { updateUserProfile } from "@/lib/auth";

interface OnboardingProps {
  onClose: () => void;
  initialEmail?: string;
  initialName?: string;
}

export interface LocalityItem {
  id: string;
  name: string;
  zone: string;
  landmarks: string;
  riskLevel: "Low" | "Moderate" | "High" | "Critical";
}

export const BHUBANESWAR_LOCALITIES: LocalityItem[] = [
  {
    id: "Ward 12 · Nayapalli / Unit 8",
    name: "Nayapalli · Unit 8 & DAV Zone",
    zone: "Central Zone (Ward 12)",
    landmarks: "DAV Public School, VIP Road, ISKCON Temple",
    riskLevel: "Moderate",
  },
  {
    id: "Patia · KIIT & Infocity",
    name: "Patia · Infocity & KIIT University",
    zone: "North Zone",
    landmarks: "KIIT Square, DLF Cybercity, Silicon Hills",
    riskLevel: "Moderate",
  },
  {
    id: "Chandrasekharpur · Damana",
    name: "Chandrasekharpur · Damana & Sailashree Vihar",
    zone: "North Zone",
    landmarks: "Care Hospital, Big Bazaar, Housing Board",
    riskLevel: "Low",
  },
  {
    id: "Jayadev Vihar · IRC Village",
    name: "Jayadev Vihar · IRC Village & Ekamra Kanan",
    zone: "Central Zone",
    landmarks: "Mayfair Crossing, Botanical Garden, BDA Colony",
    riskLevel: "Moderate",
  },
  {
    id: "Saheed Nagar · Vani Vihar",
    name: "Saheed Nagar · Vani Vihar & Janpath",
    zone: "Central East Zone",
    landmarks: "Utkal University, Maharishi College, Rupali Square",
    riskLevel: "Low",
  },
  {
    id: "Master Canteen · Station Square",
    name: "Master Canteen · Station & Ashok Nagar",
    zone: "Transit Core",
    landmarks: "Bhubaneswar Railway Station, Ram Mandir, Market Bldg",
    riskLevel: "High",
  },
  {
    id: "Unit 1 & 2 · Rajmahal & Secretariat",
    name: "Unit 1, 2 & 3 · State Secretariat Core",
    zone: "Administrative Core",
    landmarks: "Daily Market, AG Square, State Assembly, Raj Bhavan",
    riskLevel: "Low",
  },
  {
    id: "Unit 6, 8 & 9 · Capital Hospital",
    name: "Unit 6, 8 & 9 · Capital Hospital Corridor",
    zone: "Medical Axis",
    landmarks: "Capital Hospital, OUAT Campus, Siripur Square",
    riskLevel: "Critical",
  },
  {
    id: "Khandagiri · Pokhariput · Jagamara",
    name: "Khandagiri · Pokhariput & Jagamara",
    zone: "West Zone",
    landmarks: "Khandagiri Caves, ITER College, Western Bypass",
    riskLevel: "Moderate",
  },
  {
    id: "Old Town · Lingaraj Temple Zone",
    name: "Old Town · Lingaraj & Bindusagar Heritage",
    zone: "Heritage Zone",
    landmarks: "Lingaraj Temple, Bindusagar Lake, Kedar Gouri",
    riskLevel: "High",
  },
  {
    id: "Rasulgarh · Hanspal · NH-16",
    name: "Rasulgarh · Hanspal & Cuttack Road Corridor",
    zone: "East Zone",
    landmarks: "Rasulgarh Flyover, Esplanade One Mall, NH-16 Highway",
    riskLevel: "Moderate",
  },
  {
    id: "Sundarpada · Jatni Road Belt",
    name: "Sundarpada · Hi-Tech & South Suburban Belt",
    zone: "South Zone",
    landmarks: "Hi-Tech Medical College, Kapilaprasad, Jatni Link",
    riskLevel: "High",
  },
];

const ROLES = [
  { id: "resident", title: "Resident Citizen", desc: "Report neighborhood hazards and receive live municipal resolution checkpoints." },
  { id: "community_lead", title: "Community / Ward Volunteer", desc: "Coordinate local inspections and verify community issue resolutions." },
  { id: "business_owner", title: "Local Merchant / Facility", desc: "Manage storefront access, utility disruptions, and commercial corridor repairs." },
];

export function OnboardingPanel({ onClose, initialEmail = "", initialName = "" }: OnboardingProps) {
  const router = useRouter();
  const [step, setStep] = useState<number>(1);

  // Form State
  const [name, setName] = useState(initialName || "");
  const [email] = useState(initialEmail || "");
  const [phone, setPhone] = useState("+91 98765 43210");
  const [role, setRole] = useState("resident");
  
  // Location State
  const [localitySearch, setLocalitySearch] = useState("");
  const [selectedLocality, setSelectedLocality] = useState(BHUBANESWAR_LOCALITIES[0].id);
  const [customLocality, setCustomLocality] = useState("");
  const [streetAddress, setStreetAddress] = useState("Lane 4, Near DAV Public School");
  const [alertRadius, setAlertRadius] = useState("500m");
  
  // Alert & Governance Settings
  const [alertChannel, setAlertChannel] = useState<"whatsapp" | "sms" | "app">("whatsapp");
  const [alertPriority, setAlertPriority] = useState<"all" | "p1_only">("all");
  const [allowClarifications, setAllowClarifications] = useState(true);

  const filteredLocalities = BHUBANESWAR_LOCALITIES.filter((loc) => {
    const query = localitySearch.toLowerCase();
    return (
      loc.name.toLowerCase().includes(query) ||
      loc.zone.toLowerCase().includes(query) ||
      loc.landmarks.toLowerCase().includes(query)
    );
  });

  const activeLocality =
    BHUBANESWAR_LOCALITIES.find((l) => l.id === selectedLocality) || BHUBANESWAR_LOCALITIES[0];

  const handleNext = (e: React.FormEvent) => {
    e.preventDefault();
    if (step < 4) {
      setStep((prev) => prev + 1);
    }
  };

  const handleFinish = () => {
    const finalWardLocation =
      selectedLocality === "other" && customLocality.trim()
        ? `Bhubaneswar · ${customLocality.trim()}`
        : selectedLocality;

    const userData = {
      name: name || "Resident Citizen",
      email,
      phone,
      role: role === "community_lead" ? "volunteer" : role === "business_owner" ? "merchant" : "resident",
      roleTitle: role === "community_lead" ? "Ward Community Volunteer" : role === "business_owner" ? "Local Facility Lead" : "Registered Citizen · Bhubaneswar",
      ward: finalWardLocation,
      streetAddress,
      alertRadius,
      alertChannel,
      alertPriority,
      allowClarifications,
      avatarInitials: (name || "RC").slice(0, 2).toUpperCase(),
    };

    try {
      localStorage.setItem("civitas_current_user", JSON.stringify(userData));
      localStorage.setItem("civitas_onboarding_completed", "true");
      void updateUserProfile({
        name: name || "Resident Citizen",
        ward: finalWardLocation,
        roleTitle: userData.roleTitle,
        avatarInitials: (name || "RC").slice(0, 2).toUpperCase(),
      });
      window.dispatchEvent(new Event("storage"));
      window.dispatchEvent(new Event("civitas_auth_changed"));
    } catch {
      // ignore
    }

    onClose();
    router.push("/workspace");
  };

  return (
    <div className="onboarding-modal-backdrop" role="dialog" aria-modal="true" aria-labelledby="onboard-title">
      <div className="onboarding-modal-card">
        {/* TOP MODAL HEADER */}
        <div className="onboard-header-row">
          <div className="onboard-badge-group">
            <span className="step-counter-pill">STEP 0{step} OF 04</span>
            <span className="onboard-sub-kicker">CITIZEN PROFILE ONBOARDING</span>
          </div>
          <button type="button" className="modal-close-btn" onClick={onClose} aria-label="Close onboarding">
            <FlatIcon name="cross" size={14} />
          </button>
        </div>

        {/* PROGRESS BAR */}
        <div className="onboard-progress-track">
          <div
            className="onboard-progress-fill"
            style={{ width: `${(step / 4) * 100}%` }}
          />
        </div>

        {/* STEP 1: IDENTITY & ROLE */}
        {step === 1 && (
          <form onSubmit={handleNext} className="onboard-step-body">
            <div className="step-title-group">
              <h2 id="onboard-title" className="step-main-title">Create Your Civic Identity</h2>
              <p className="step-subtitle">
                Set up your verified resident identity for official municipal correspondence and dispatch updates across Bhubaneswar.
              </p>
            </div>

            <div className="form-fields-stack">
              <div className="field-block">
                <label className="field-label" htmlFor="onboard-name">
                  Full Display Name
                </label>
                <input
                  id="onboard-name"
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Alex Morgan"
                  className="modal-text-input"
                />
              </div>

              <div className="field-block">
                <label className="field-label" htmlFor="onboard-phone">
                  Phone / WhatsApp (For Real-Time Status Alerts)
                </label>
                <input
                  id="onboard-phone"
                  type="tel"
                  required
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  placeholder="+91 98765 43210"
                  className="modal-text-input"
                />
              </div>

              <div className="field-block">
                <span className="field-label">Select Your Civic Participation Role</span>
                <div className="role-cards-grid">
                  {ROLES.map((r) => {
                    const isSelected = role === r.id;
                    return (
                      <div
                        key={r.id}
                        className={`role-select-card ${isSelected ? "selected" : ""}`}
                        onClick={() => setRole(r.id)}
                      >
                        <div className="role-radio-circle">{isSelected && <span className="inner-dot" />}</div>
                        <div className="role-card-text">
                          <b>{r.title}</b>
                          <small>{r.desc}</small>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>

            <div className="modal-actions-footer">
              <span className="step-hint">Step 1 of 4: Identity Setup</span>
              <button type="submit" className="button large continue-btn">
                Next: Bhubaneswar Location →
              </button>
            </div>
          </form>
        )}

        {/* STEP 2: BHUBANESWAR LOCATION & GEOFENCE */}
        {step === 2 && (
          <form onSubmit={handleNext} className="onboard-step-body">
            <div className="step-title-group">
              <h2 id="onboard-title" className="step-main-title">Select Your Bhubaneswar Locality</h2>
              <p className="step-subtitle">
                Choose your residential or business neighborhood across Greater Bhubaneswar to set your PostGIS proximity alert buffer.
              </p>
            </div>

            <div className="form-fields-stack">
              {/* SEARCH FILTER */}
              <div className="field-block">
                <label className="field-label" htmlFor="locality-search-input">
                  Search Bhubaneswar Zones ({BHUBANESWAR_LOCALITIES.length} Available)
                </label>
                <div className="search-input-wrapper">
                  <FlatIcon name="search" size={15} color="#687067" />
                  <input
                    id="locality-search-input"
                    type="text"
                    value={localitySearch}
                    onChange={(e) => setLocalitySearch(e.target.value)}
                    placeholder="Search e.g. Patia, Nayapalli, Saheed Nagar, Khandagiri..."
                    className="modal-search-field"
                  />
                  {localitySearch && (
                    <button
                      type="button"
                      className="clear-search-x"
                      onClick={() => setLocalitySearch("")}
                      aria-label="Clear search"
                    >
                      <FlatIcon name="cross" size={11} />
                    </button>
                  )}
                </div>
              </div>

              {/* LOCALITY CARDS GRID */}
              <div className="field-block">
                <span className="field-label">Choose Primary Locality / Ward</span>
                <div className="locality-scroll-grid">
                  {filteredLocalities.map((loc) => {
                    const isSelected = selectedLocality === loc.id;
                    return (
                      <div
                        key={loc.id}
                        className={`locality-card ${isSelected ? "selected" : ""}`}
                        onClick={() => setSelectedLocality(loc.id)}
                      >
                        <div className="loc-top-row">
                          <span className="loc-zone-badge">{loc.zone}</span>
                          <span className={`loc-risk-badge ${loc.riskLevel.toLowerCase()}`}>
                            {loc.riskLevel} Risk
                          </span>
                        </div>
                        <b className="loc-title">{loc.name}</b>
                        <small className="loc-landmarks">Near: {loc.landmarks}</small>
                      </div>
                    );
                  })}

                  {/* OTHER CUSTOM LOCALITY CARD */}
                  <div
                    className={`locality-card other-card ${selectedLocality === "other" ? "selected" : ""}`}
                    onClick={() => setSelectedLocality("other")}
                  >
                    <div className="loc-top-row">
                      <span className="loc-zone-badge">Custom Zone</span>
                      <span className="loc-risk-badge">All 67 Wards</span>
                    </div>
                    <b className="loc-title">+ Other Locality in Bhubaneswar</b>
                    <small className="loc-landmarks">Enter custom ward, society or colony name</small>
                  </div>
                </div>
              </div>

              {/* CUSTOM LOCALITY TEXT FIELD IF 'OTHER' SELECTED */}
              {selectedLocality === "other" && (
                <div className="field-block custom-locality-fade">
                  <label className="field-label" htmlFor="custom-loc-input">
                    Specify Your Locality / Colony Name in Bhubaneswar
                  </label>
                  <input
                    id="custom-loc-input"
                    type="text"
                    required
                    value={customLocality}
                    onChange={(e) => setCustomLocality(e.target.value)}
                    placeholder="e.g. Kalinga Nagar, Mancheswar, Tomando, Ghatikia..."
                    className="modal-text-input"
                  />
                </div>
              )}

              <div className="field-block">
                <label className="field-label" htmlFor="onboard-street">
                  Street / Landmark / Colony Address
                </label>
                <input
                  id="onboard-street"
                  type="text"
                  required
                  value={streetAddress}
                  onChange={(e) => setStreetAddress(e.target.value)}
                  placeholder="e.g. Plot 24, Near Sector Community Centre"
                  className="modal-text-input"
                />
              </div>

              <div className="field-block">
                <span className="field-label">PostGIS Proximity Alert Buffer</span>
                <div className="radius-pill-group">
                  {["250m (Immediate Block)", "500m (School & Hospital Buffer)", "1km (Full Neighborhood)"].map((rad) => {
                    const value = rad.split(" ")[0];
                    const isSelected = alertRadius === value;
                    return (
                      <button
                        key={rad}
                        type="button"
                        className={`radius-pill ${isSelected ? "selected" : ""}`}
                        onClick={() => setAlertRadius(value)}
                      >
                        {rad}
                      </button>
                    );
                  })}
                </div>
              </div>
            </div>

            <div className="modal-actions-footer">
              <button type="button" className="outline" onClick={() => setStep(1)}>
                ← Back
              </button>
              <button type="submit" className="button large continue-btn">
                Next: Alert Preferences →
              </button>
            </div>
          </form>
        )}

        {/* STEP 3: ALERT PREFERENCES & CLARIFICATION */}
        {step === 3 && (
          <form onSubmit={handleNext} className="onboard-step-body">
            <div className="step-title-group">
              <h2 id="onboard-title" className="step-main-title">Notification & Verification Settings</h2>
              <p className="step-subtitle">
                Configure how municipal departments send status updates and whether supervisors can ask quick photo questions.
              </p>
            </div>

            <div className="form-fields-stack">
              <div className="field-block">
                <span className="field-label">Preferred Notification Channel</span>
                <div className="channel-cards-row">
                  {[
                    { id: "whatsapp", label: "WhatsApp Alerts", desc: "Instant photos and crew dispatch ETAs" },
                    { id: "sms", label: "SMS Text Message", desc: "Standard text checkpoints" },
                    { id: "app", label: "In-App Dashboard", desc: "Silent updates in web portal" },
                  ].map((ch) => {
                    const isSelected = alertChannel === ch.id;
                    return (
                      <div
                        key={ch.id}
                        className={`channel-card ${isSelected ? "selected" : ""}`}
                        onClick={() => setAlertChannel(ch.id as "whatsapp" | "sms" | "app")}
                      >
                        <b>{ch.label}</b>
                        <small>{ch.desc}</small>
                      </div>
                    );
                  })}
                </div>
              </div>

              <div className="field-block">
                <span className="field-label">Alert Sensitivity Level</span>
                <div className="sensitivity-selector">
                  <button
                    type="button"
                    className={`sense-btn ${alertPriority === "all" ? "active" : ""}`}
                    onClick={() => setAlertPriority("all")}
                  >
                    <b>All Neighborhood Incidents</b>
                    <small>Water leaks, potholes, trees, streetlights</small>
                  </button>
                  <button
                    type="button"
                    className={`sense-btn ${alertPriority === "p1_only" ? "active" : ""}`}
                    onClick={() => setAlertPriority("p1_only")}
                  >
                    <b>P1 Critical Emergencies Only</b>
                    <small>Active water main bursts, road blockages</small>
                  </button>
                </div>
              </div>

              <div className="clarification-optin-box">
                <div className="optin-left">
                  <FlatIcon name="shield" size={20} color="#0f5f4f" />
                  <div>
                    <b>1-Click Single-Question Clarifications</b>
                    <p>
                      Allow supervisors to send a single photo question if needed to prevent dispatching the wrong equipment.
                    </p>
                  </div>
                </div>
                <input
                  type="checkbox"
                  checked={allowClarifications}
                  onChange={(e) => setAllowClarifications(e.target.checked)}
                  className="optin-toggle"
                />
              </div>
            </div>

            <div className="modal-actions-footer">
              <button type="button" className="outline" onClick={() => setStep(2)}>
                ← Back
              </button>
              <button type="submit" className="button large continue-btn">
                Next: Review & Launch →
              </button>
            </div>
          </form>
        )}

        {/* STEP 4: HOW CIVITAS WORKS & CIVIC PASSPORT */}
        {step === 4 && (
          <div className="onboard-step-body">
            <div className="step-title-group">
              <h2 id="onboard-title" className="step-main-title">How Civitas Operates</h2>
              <p className="step-subtitle">
                Civitas is an evidence-backed civic intelligence system. Here is the operational lifecycle from citizen report to verified physical repair:
              </p>
            </div>

            {/* HOW THE APP WORKS 4-STAGE PIPELINE */}
            <div className="civitas-how-it-works-grid">
              <div className="how-stage-card">
                <div className="stage-header">
                  <span className="stage-num">01</span>
                  <FlatIcon name="map" size={16} color="#0f5f4f" />
                  <b>Spatial Deduplication</b>
                </div>
                <p>
                  PostGIS 3.4 clusters duplicate reports within a 15m radius into 1 consolidated incident dossier. No duplicate work orders.
                </p>
              </div>

              <div className="how-stage-card">
                <div className="stage-header">
                  <span className="stage-num">02</span>
                  <FlatIcon name="workflow" size={16} color="#0f5f4f" />
                  <b>LangGraph Orchestration</b>
                </div>
                <p>
                  Dual critic models validate facts, match municipal policy playbooks, and compute severity without hallucinating timelines.
                </p>
              </div>

              <div className="how-stage-card">
                <div className="stage-header">
                  <span className="stage-num">03</span>
                  <FlatIcon name="shield" size={16} color="#0f5f4f" />
                  <b>Supervisor Sign-Off</b>
                </div>
                <p>
                  Human supervisors review high-impact work orders before field crews dispatch. 1-click photo queries resolve missing details.
                </p>
              </div>

              <div className="how-stage-card">
                <div className="stage-header">
                  <span className="stage-num">04</span>
                  <FlatIcon name="check" size={16} color="#0f5f4f" />
                  <b>Computer Vision Audit</b>
                </div>
                <p>
                  Before ticket closure, zero-shot CV verifies the repair photo against initial damage to guarantee physical resolution.
                </p>
              </div>
            </div>

            {/* CIVIC PASSPORT CONFIRMATION CARD */}
            <div className="civic-passport-badge-card">
              <div className="passport-top-row">
                <div className="passport-avatar">
                  <span>{(name || "RC").slice(0, 2).toUpperCase()}</span>
                </div>
                <div className="passport-meta">
                  <div className="passport-kicker-row">
                    <span className="passport-verified-tag" style={{ display: "inline-flex", alignItems: "center", gap: "4px" }}>
                      <FlatIcon name="check" size={10} color="#0f5f4f" /> VERIFIED RESIDENT
                    </span>
                    <span className="passport-ward-tag">BHUBANESWAR BMC</span>
                  </div>
                  <b className="passport-name">{name || "Registered Resident"}</b>
                  <p className="passport-email">{email} · {phone}</p>
                </div>
              </div>

              <div className="passport-specs-grid">
                <div className="spec-tile">
                  <span>REGISTERED GEOFENCE</span>
                  <b>{selectedLocality === "other" && customLocality ? customLocality : activeLocality.name}</b>
                </div>
                <div className="spec-tile">
                  <span>NOTIFICATIONS</span>
                  <b>{alertChannel.toUpperCase()} ({alertRadius})</b>
                </div>
                <div className="spec-tile">
                  <span>ROLE AFFILIATION</span>
                  <b>{role === "community_lead" ? "Ward Volunteer" : role === "business_owner" ? "Facility Lead" : "Registered Citizen"}</b>
                </div>
                <div className="spec-tile">
                  <span>SAFETY GATE CLEARANCE</span>
                  <b>Active (Critic Gate Passed)</b>
                </div>
              </div>
            </div>

            <div className="modal-actions-footer">
              <button type="button" className="outline" onClick={() => setStep(3)}>
                ← Back
              </button>
              <button type="button" className="button large continue-btn" onClick={handleFinish}>
                Complete Onboarding & Enter Command Center →
              </button>
            </div>
          </div>
        )}
      </div>

      <style jsx>{`
        .onboarding-modal-backdrop {
          position: fixed;
          inset: 0;
          z-index: 9999;
          background: rgba(23, 32, 25, 0.78);
          backdrop-filter: blur(8px);
          display: grid;
          place-items: center;
          padding: 20px;
          animation: fadeIn 0.2s ease-out;
        }
        @keyframes fadeIn {
          from {
            opacity: 0;
          }
          to {
            opacity: 1;
          }
        }
        .onboarding-modal-card {
          width: min(100%, 680px);
          background: #ffffff;
          border: 2px solid #172019;
          box-shadow: 8px 8px 0 #172019;
          border-radius: 8px;
          padding: 28px 32px;
          display: flex;
          flex-direction: column;
          gap: 16px;
          max-height: 90vh;
          overflow-y: auto;
          animation: slideUp 0.25s cubic-bezier(0.16, 1, 0.3, 1);
        }
        @keyframes slideUp {
          from {
            transform: translateY(14px);
            opacity: 0;
          }
          to {
            transform: translateY(0);
            opacity: 1;
          }
        }
        .onboard-header-row {
          display: flex;
          justify-content: space-between;
          align-items: center;
        }
        .onboard-badge-group {
          display: flex;
          align-items: center;
          gap: 8px;
        }
        .step-counter-pill {
          font-size: 0.65rem;
          font-weight: 900;
          letter-spacing: 0.1em;
          background: #172019;
          color: #ffffff;
          padding: 3px 8px;
          border-radius: 4px;
        }
        .onboard-sub-kicker {
          font-size: 0.65rem;
          font-weight: 800;
          letter-spacing: 0.1em;
          color: #0f5f4f;
        }
        .modal-close-btn {
          background: transparent;
          border: 1px solid #172019;
          width: 28px;
          height: 28px;
          border-radius: 4px;
          cursor: pointer;
          font-size: 0.9rem;
          display: grid;
          place-items: center;
          font-weight: 800;
          transition: background 0.15s ease;
        }
        .modal-close-btn:hover {
          background: #fee2e2;
          color: #991b1b;
        }
        .onboard-progress-track {
          width: 100%;
          height: 6px;
          background: #f0ece1;
          border: 1px solid #172019;
          border-radius: 3px;
          overflow: hidden;
        }
        .onboard-progress-fill {
          height: 100%;
          background: #0f5f4f;
          transition: width 0.3s ease;
        }
        .onboard-step-body {
          display: flex;
          flex-direction: column;
          gap: 18px;
        }
        .step-title-group {
          display: flex;
          flex-direction: column;
          gap: 4px;
        }
        .step-main-title {
          font-size: 1.7rem;
          font-family: Georgia, serif;
          margin: 0;
          color: #172019;
        }
        .step-subtitle {
          font-size: 0.85rem;
          color: #555e54;
          margin: 0;
          line-height: 1.45;
        }
        .form-fields-stack {
          display: flex;
          flex-direction: column;
          gap: 14px;
        }
        .field-block {
          display: flex;
          flex-direction: column;
          gap: 6px;
        }
        .field-label {
          font-size: 0.78rem;
          font-weight: 800;
          color: #172019;
        }
        .modal-text-input {
          width: 100%;
          border: 1px solid #172019;
          background: #fbf9f4;
          padding: 10px 14px;
          font-size: 0.88rem;
          border-radius: 4px;
          outline: none;
          font-family: inherit;
        }
        .modal-text-input:focus {
          background: #ffffff;
          border-color: #0f5f4f;
          box-shadow: 0 0 0 2px rgba(15, 95, 79, 0.15);
        }
        .search-input-wrapper {
          position: relative;
          display: flex;
          align-items: center;
          border: 1px solid #172019;
          background: #fbf9f4;
          border-radius: 4px;
          padding: 0 12px;
          gap: 8px;
        }
        .modal-search-field {
          flex: 1;
          border: 0;
          background: transparent;
          padding: 9px 0;
          font-size: 0.86rem;
          outline: none;
          font-family: inherit;
        }
        .clear-search-x {
          border: 0;
          background: transparent;
          cursor: pointer;
          font-size: 0.75rem;
          color: #687067;
          padding: 2px 6px;
        }
        .locality-scroll-grid {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 8px;
          max-height: 240px;
          overflow-y: auto;
          padding-right: 4px;
        }
        .locality-card {
          border: 1px solid #172019;
          background: #fbf9f4;
          padding: 10px 12px;
          border-radius: 6px;
          cursor: pointer;
          display: flex;
          flex-direction: column;
          gap: 3px;
          text-align: left;
          transition: all 0.15s ease;
        }
        .locality-card:hover {
          background: #ffffff;
          box-shadow: 2px 2px 0 #172019;
        }
        .locality-card.selected {
          border-left: 5px solid #0f5f4f;
          background: #ffffff;
          box-shadow: 3px 3px 0 #172019;
        }
        .locality-card.other-card {
          border-style: dashed;
        }
        .loc-top-row {
          display: flex;
          justify-content: space-between;
          align-items: center;
        }
        .loc-zone-badge {
          font-size: 0.58rem;
          font-weight: 850;
          color: #0f5f4f;
          background: #dce8dd;
          padding: 2px 5px;
          border-radius: 3px;
        }
        .loc-risk-badge {
          font-size: 0.56rem;
          font-weight: 800;
          color: #687067;
        }
        .loc-risk-badge.high, .loc-risk-badge.critical {
          color: #991b1b;
        }
        .loc-title {
          font-size: 0.8rem;
          color: #172019;
          line-height: 1.25;
        }
        .loc-landmarks {
          font-size: 0.66rem;
          color: #687067;
          line-height: 1.25;
        }
        .custom-locality-fade {
          animation: fadeIn 0.2s ease-out;
        }
        .role-cards-grid {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }
        .role-select-card {
          border: 1px solid #172019;
          background: #fbf9f4;
          padding: 10px 14px;
          border-radius: 6px;
          cursor: pointer;
          display: flex;
          align-items: center;
          gap: 12px;
          transition: all 0.15s ease;
        }
        .role-select-card:hover {
          background: #ffffff;
          box-shadow: 2px 2px 0 #172019;
        }
        .role-select-card.selected {
          background: #ffffff;
          border-left: 6px solid #0f5f4f;
          box-shadow: 3px 3px 0 #172019;
        }
        .role-radio-circle {
          width: 18px;
          height: 18px;
          border-radius: 50%;
          border: 2px solid #172019;
          display: grid;
          place-items: center;
          flex-shrink: 0;
        }
        .inner-dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
          background: #0f5f4f;
        }
        .role-card-text b {
          display: block;
          font-size: 0.84rem;
          color: #172019;
        }
        .role-card-text small {
          display: block;
          font-size: 0.72rem;
          color: #687067;
          line-height: 1.3;
        }
        .radius-pill-group {
          display: flex;
          flex-wrap: wrap;
          gap: 6px;
        }
        .radius-pill {
          padding: 6px 12px;
          border: 1px solid #172019;
          background: #fbf9f4;
          font-size: 0.74rem;
          font-weight: 750;
          border-radius: 4px;
          cursor: pointer;
        }
        .radius-pill.selected {
          background: #172019;
          color: #ffffff;
        }
        .channel-cards-row {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 8px;
        }
        .channel-card {
          border: 1px solid #172019;
          background: #fbf9f4;
          padding: 10px;
          border-radius: 6px;
          cursor: pointer;
          display: flex;
          flex-direction: column;
          gap: 2px;
          text-align: left;
        }
        .channel-card.selected {
          background: #172019;
          color: #ffffff;
          box-shadow: 2px 2px 0 #0f5f4f;
        }
        .channel-card.selected small {
          color: #dce8dd;
        }
        .channel-card b {
          font-size: 0.78rem;
        }
        .channel-card small {
          font-size: 0.66rem;
          color: #687067;
        }
        .sensitivity-selector {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 8px;
        }
        .sense-btn {
          border: 1px solid #172019;
          background: #fbf9f4;
          padding: 10px 12px;
          border-radius: 6px;
          cursor: pointer;
          text-align: left;
          display: flex;
          flex-direction: column;
          gap: 2px;
        }
        .sense-btn.active {
          background: #ffffff;
          border-left: 5px solid #0f5f4f;
          box-shadow: 2px 2px 0 #172019;
        }
        .sense-btn b {
          font-size: 0.78rem;
          color: #172019;
        }
        .sense-btn small {
          font-size: 0.68rem;
          color: #687067;
        }
        .clarification-optin-box {
          border: 1px solid #0f5f4f;
          background: #f4f8f5;
          padding: 12px 14px;
          border-radius: 6px;
          display: flex;
          justify-content: space-between;
          align-items: center;
          gap: 12px;
        }
        .optin-left {
          display: flex;
          align-items: center;
          gap: 12px;
        }
        .optin-left b {
          font-size: 0.8rem;
          color: #0f5f4f;
          display: block;
        }
        .optin-left p {
          font-size: 0.74rem;
          color: #334035;
          margin: 0;
          line-height: 1.35;
        }
        .optin-toggle {
          width: 18px;
          height: 18px;
          cursor: pointer;
          accent-color: #0f5f4f;
        }
        .civitas-how-it-works-grid {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 10px;
          margin-bottom: 6px;
        }
        .how-stage-card {
          border: 1px solid #172019;
          background: #fbf9f4;
          padding: 12px 14px;
          border-radius: 6px;
          display: flex;
          flex-direction: column;
          gap: 6px;
        }
        .stage-header {
          display: flex;
          align-items: center;
          gap: 8px;
        }
        .stage-num {
          font-size: 0.65rem;
          font-weight: 900;
          color: #ffffff;
          background: #0f5f4f;
          padding: 2px 5px;
          border-radius: 3px;
        }
        .stage-header b {
          font-size: 0.8rem;
          color: #172019;
        }
        .how-stage-card p {
          font-size: 0.73rem;
          color: #555e54;
          margin: 0;
          line-height: 1.35;
        }
        .civic-passport-badge-card {
          border: 2px solid #172019;
          background: #fbf9f4;
          box-shadow: 4px 4px 0 #172019;
          padding: 20px;
          border-radius: 8px;
          display: flex;
          flex-direction: column;
          gap: 16px;
        }
        .passport-top-row {
          display: flex;
          align-items: center;
          gap: 16px;
        }
        .passport-avatar {
          width: 52px;
          height: 52px;
          border-radius: 50%;
          background: #0f5f4f;
          color: #ffffff;
          display: grid;
          place-items: center;
          font-size: 1.3rem;
          font-family: Georgia, serif;
          font-weight: 700;
          border: 2px solid #172019;
          box-shadow: 2px 2px 0 #172019;
        }
        .passport-meta {
          display: flex;
          flex-direction: column;
          gap: 2px;
        }
        .passport-kicker-row {
          display: flex;
          gap: 8px;
          align-items: center;
        }
        .passport-verified-tag {
          font-size: 0.6rem;
          font-weight: 900;
          color: #0f5f4f;
          background: #dce8dd;
          padding: 2px 6px;
          border-radius: 3px;
        }
        .passport-ward-tag {
          font-size: 0.6rem;
          font-weight: 800;
          color: #687067;
        }
        .passport-name {
          font-size: 1.15rem;
          color: #172019;
        }
        .passport-email {
          font-size: 0.75rem;
          color: #687067;
          margin: 0;
        }
        .passport-specs-grid {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 10px;
          border-top: 1px solid #e2ded4;
          padding-top: 14px;
        }
        .spec-tile span {
          display: block;
          font-size: 0.58rem;
          font-weight: 900;
          letter-spacing: 0.08em;
          color: #687067;
        }
        .spec-tile b {
          font-size: 0.82rem;
          color: #172019;
        }
        .modal-actions-footer {
          display: flex;
          justify-content: space-between;
          align-items: center;
          gap: 12px;
          padding-top: 8px;
        }
        .modal-actions-footer.single-action {
          justify-content: center;
        }
        .step-hint {
          font-size: 0.72rem;
          font-weight: 800;
          color: #687067;
        }
        .launch-workspace-btn {
          width: 100%;
        }
        @media (max-width: 600px) {
          .civitas-how-it-works-grid,
          .locality-scroll-grid,
          .channel-cards-row,
          .sensitivity-selector,
          .passport-specs-grid {
            grid-template-columns: 1fr;
          }
        }
      `}</style>
    </div>
  );
}
