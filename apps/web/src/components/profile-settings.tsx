"use client";

import { FormEvent, useState } from "react";

export function ProfileSettings() {
  const [name, setName] = useState("Demo resident");
  const [area, setArea] = useState("Ward 12, Bhubaneswar");
  const [message, setMessage] = useState("");
  const save = (event: FormEvent) => { event.preventDefault(); setMessage("Saved locally for this preview. Account persistence requires sign-in."); };
  return <section className="profile-settings"><form onSubmit={save}><div className="settings-heading"><div><span>PERSONALIZATION</span><h2>Account preferences</h2></div><button className="button small">Save changes</button></div><div className="settings-grid"><label>Display name<input value={name} onChange={(event) => setName(event.target.value)} /></label><label>Home area<input value={area} onChange={(event) => setArea(event.target.value)} /></label></div>{message && <p className="form-feedback" role="status">{message}</p>}</form><div className="settings-actions"><div><h3>Password</h3><p>Use a reset link only after confirming the account email.</p><button className="outline" onClick={() => setMessage("Password reset is available after signing in.")}>Reset password</button></div><div><h3>Report history</h3><p>Preview history is local to this browser and can be removed any time.</p><button className="text-button danger-text" onClick={() => setMessage("Preview history cleared from this browser.")}>Clear preview history</button></div></div></section>;
}
