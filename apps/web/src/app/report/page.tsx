"use client";

import { useState } from "react";

import { Nav } from "@/components/site";

export default function Report() {
  const [submitted, setSubmitted] = useState(false);

  return <><Nav /><main className="formpage"><p className="eyebrow">Citizen report · Step 1 of 4</p><h1>Tell us what needs attention.</h1>{submitted ? <section className="notice"><h2>Report ready for review</h2><p>Your issue has been recorded. Civitas may ask a focused clarification when more evidence is needed.</p></section> : <form onSubmit={(event) => { event.preventDefault(); setSubmitted(true); }}><label>Description<textarea required minLength={3} placeholder="What happened? Include landmarks or safety concerns if you know them." /></label><label>Category <select defaultValue=""><option value="">I’m not sure</option><option>Water leak</option><option>Pothole or road damage</option><option>Garbage overflow</option><option>Broken streetlight</option><option>Fallen tree</option></select></label><div className="twocol"><label>Latitude<input required type="number" step="any" placeholder="20.296" /></label><label>Longitude<input required type="number" step="any" placeholder="85.824" /></label></div><label>Photo or video <input type="file" accept="image/*,video/*" /></label><button className="button">Continue to review</button></form>}</main></>;
}
