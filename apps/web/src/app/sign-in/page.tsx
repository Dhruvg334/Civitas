"use client";

import { FormEvent, useState } from "react";
import Link from "next/link";

import { Footer, Nav } from "@/components/site";
import { OnboardingPanel } from "@/components/onboarding-panel";

export default function SignIn() {
  const [create, setCreate] = useState(false);
  const [notice, setNotice] = useState("");
  const [onboarding, setOnboarding] = useState(false);
  const submit = (event: FormEvent) => { event.preventDefault(); if (create) setOnboarding(true); else setNotice("Sign-in is ready for backend authentication integration."); };
  return <><Nav /><main className="auth-shell"><section className="auth-intro"><p className="section-kicker">Civitas account</p><h1>Keep your reports in view.</h1><p>An account lets residents answer clarifications, follow incident status and manage their local preferences. Municipal access is role-controlled.</p><ul><li>Track reports and incident updates</li><li>Receive clarification requests</li><li>Control account and location preferences</li></ul></section><section className="auth-card"><div className="auth-switch" role="tablist"><button className={!create ? "active" : ""} onClick={() => setCreate(false)}>Sign in</button><button className={create ? "active" : ""} onClick={() => setCreate(true)}>Create account</button></div><form onSubmit={submit}><label>Email address<input type="email" required autoComplete="email" placeholder="you@example.com" /></label>{create && <label>Display name<input required autoComplete="name" placeholder="How should Civitas address you?" /></label>}<label>Password<input type="password" required minLength={8} autoComplete={create ? "new-password" : "current-password"} placeholder="At least 8 characters" /></label><button className="button">{create ? "Create account" : "Sign in"}</button>{!create && <button type="button" className="text-button" onClick={() => setNotice("Password reset is available after authentication is connected.")}>Forgot password?</button>}{notice && <p className="form-feedback" role="status">{notice}</p>}</form><p className="auth-legal">By continuing, you acknowledge the <Link href="/terms">Terms of use</Link> and <Link href="/privacy">Privacy & location notice</Link>.</p></section></main>{onboarding && <OnboardingPanel onClose={() => { setOnboarding(false); setNotice("Onboarding preferences saved locally for this preview."); }} />}<Footer /></>;
}
