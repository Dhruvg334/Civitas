"use client";

import { useState, FormEvent } from "react";
import Link from "next/link";
import { Footer, Nav } from "@/components/site";
import { FlatIcon } from "@/components/flat-icons";

export default function ResetPassword() {
  const [email, setEmail] = useState("");
  const [step, setStep] = useState<"request" | "verify" | "success">("request");
  const [code, setCode] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [notice, setNotice] = useState("");

  const handleRequestReset = (e: FormEvent) => {
    e.preventDefault();
    if (!email) return;
    setStep("verify");
    setNotice(`A 6-digit security recovery code has been sent to ${email}.`);
  };

  const handleResetSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (newPassword !== confirmPassword) {
      setNotice("Passwords do not match. Please re-enter.");
      return;
    }
    if (newPassword.length < 8) {
      setNotice("Password must contain at least 8 characters.");
      return;
    }
    setStep("success");
    setNotice("Your password has been successfully updated. You can now sign in with your new credentials.");
  };

  return (
    <>
      <Nav />
      <main className="reset-main-shell">
        <div className="reset-card">
          <div className="reset-header">
            <span className="reset-kicker">ACCOUNT SECURITY</span>
            <h1 className="reset-title">Reset Your Password</h1>
            <p className="reset-subtitle">
              Enter your registered email address to receive a secure recovery verification code.
            </p>
          </div>

          {notice && (
            <div className="reset-alert" role="status">
              {notice}
            </div>
          )}

          {step === "request" && (
            <form onSubmit={handleRequestReset} className="reset-form">
              <div className="field-group">
                <label className="field-label">
                  Registered Email Address
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="e.g. name@example.com"
                    className="text-input"
                  />
                </label>
              </div>

              <button type="submit" className="button large submit-btn">
                Send Recovery Code →
              </button>

              <div className="form-footer-links">
                <Link href="/sign-in" className="back-link">
                  ← Back to Sign In
                </Link>
              </div>
            </form>
          )}

          {step === "verify" && (
            <form onSubmit={handleResetSubmit} className="reset-form">
              <div className="field-group">
                <label className="field-label">
                  6-Digit Verification Code
                  <input
                    type="text"
                    required
                    maxLength={6}
                    value={code}
                    onChange={(e) => setCode(e.target.value)}
                    placeholder="123456"
                    className="text-input code-input"
                  />
                </label>
              </div>

              <div className="field-group">
                <label className="field-label">
                  New Password
                  <div className="password-input-wrapper">
                    <input
                      type={showPassword ? "text" : "password"}
                      required
                      minLength={8}
                      value={newPassword}
                      onChange={(e) => setNewPassword(e.target.value)}
                      placeholder="Minimum 8 characters"
                      className="text-input"
                    />
                    <button
                      type="button"
                      className="eye-toggle-btn"
                      onClick={() => setShowPassword(!showPassword)}
                      aria-label={showPassword ? "Hide password" : "Show password"}
                    >
                      <FlatIcon name={showPassword ? "eye-off" : "eye"} size={16} color="#687067" />
                    </button>
                  </div>
                </label>
              </div>

              <div className="field-group">
                <label className="field-label">
                  Confirm New Password
                  <input
                    type={showPassword ? "text" : "password"}
                    required
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder="Re-enter new password"
                    className="text-input"
                  />
                </label>
              </div>

              <button type="submit" className="button large submit-btn">
                Update Password & Secure Account →
              </button>

              <div className="form-footer-links">
                <button
                  type="button"
                  className="link-btn"
                  onClick={() => setStep("request")}
                >
                  ← Request a different code
                </button>
              </div>
            </form>
          )}

          {step === "success" && (
            <div className="reset-success-box">
              <div className="success-icon-wrap">
                <FlatIcon name="check" size={24} color="#ffffff" />
              </div>
              <h3>Password Reset Complete</h3>
              <p>Your password has been changed securely. Please sign in to resume monitoring your civic reports.</p>
              <Link href="/sign-in" className="button large">
                Sign In With New Password →
              </Link>
            </div>
          )}
        </div>
      </main>
      <Footer />

      <style jsx>{`
        .reset-main-shell {
          min-height: 65vh;
          display: grid;
          place-items: center;
          padding: 60px 20px;
        }
        .reset-card {
          width: min(100%, 480px);
          border: 2px solid #172019;
          background: #ffffff;
          box-shadow: 6px 6px 0 #172019;
          padding: 36px;
          border-radius: 8px;
        }
        .reset-header {
          margin-bottom: 24px;
        }
        .reset-kicker {
          font-size: 0.65rem;
          font-weight: 900;
          letter-spacing: 0.12em;
          color: #0f5f4f;
          display: block;
          margin-bottom: 6px;
        }
        .reset-title {
          font-size: 2rem;
          font-family: Georgia, serif;
          margin: 0 0 8px;
          color: #172019;
        }
        .reset-subtitle {
          font-size: 0.9rem;
          color: #555e54;
          margin: 0;
          line-height: 1.5;
        }
        .reset-alert {
          padding: 12px 14px;
          background: #f4f8f5;
          border: 1px solid #0f5f4f;
          color: #0f5f4f;
          font-size: 0.82rem;
          font-weight: 750;
          border-radius: 4px;
          margin-bottom: 20px;
          line-height: 1.45;
        }
        .reset-form {
          display: flex;
          flex-direction: column;
          gap: 18px;
        }
        .field-group {
          display: flex;
          flex-direction: column;
        }
        .field-label {
          font-size: 0.82rem;
          font-weight: 800;
          color: #172019;
          display: flex;
          flex-direction: column;
          gap: 6px;
        }
        .text-input {
          width: 100%;
          border: 1px solid #172019;
          background: #fbf9f4;
          padding: 11px 14px;
          font-size: 0.9rem;
          border-radius: 4px;
          outline: none;
          font-family: inherit;
        }
        .code-input {
          font-size: 1.4rem;
          font-weight: 900;
          letter-spacing: 0.25em;
          text-align: center;
        }
        .password-input-wrapper {
          position: relative;
          display: flex;
          align-items: center;
        }
        .eye-toggle-btn {
          position: absolute;
          right: 12px;
          background: transparent;
          border: 0;
          cursor: pointer;
          padding: 4px;
          display: grid;
          place-items: center;
        }
        .submit-btn {
          width: 100%;
          margin-top: 6px;
        }
        .form-footer-links {
          display: flex;
          justify-content: center;
          margin-top: 14px;
        }
        .back-link, .link-btn {
          font-size: 0.82rem;
          font-weight: 800;
          color: #0f5f4f;
          background: transparent;
          border: 0;
          cursor: pointer;
          text-decoration: none;
        }
        .back-link:hover, .link-btn:hover {
          color: #e84d7a;
        }
        .reset-success-box {
          text-align: center;
          padding: 16px 0;
        }
        .success-icon-wrap {
          width: 48px;
          height: 48px;
          border-radius: 50%;
          background: #0f5f4f;
          display: grid;
          place-items: center;
          margin: 0 auto 16px;
        }
        .reset-success-box h3 {
          font-size: 1.5rem;
          font-family: Georgia, serif;
          margin: 0 0 8px;
          color: #172019;
        }
        .reset-success-box p {
          font-size: 0.88rem;
          color: #555e54;
          margin: 0 0 24px;
          line-height: 1.5;
        }
      `}</style>
    </>
  );
}
