"use client";

import { useState, useSyncExternalStore } from "react";

type Preference = "unset" | "essential" | "all";

export function CookieControls() {
  const storedPreference = useSyncExternalStore(
    () => () => undefined,
    () => (localStorage.getItem("civitas-cookie-preference") as Preference | null) ?? "unset",
    () => "unset",
  );
  const [selection, setSelection] = useState<Preference | null>(null);
  const preference = selection ?? storedPreference;
  const save = (value: Exclude<Preference, "unset">) => { localStorage.setItem("civitas-cookie-preference", value); setSelection(value); };
  if (preference === "unset") return <section className="cookie-banner" aria-label="Cookie preferences"><p><b>Your privacy matters.</b> Civitas uses essential storage for this demo. Optional analytics remain off unless you accept them.</p><div><button className="outline" onClick={() => save("essential")}>Essential only</button><button className="button" onClick={() => save("all")}>Accept optional cookies</button></div></section>;
  return <button className="text-button footer-cookie" onClick={() => setSelection("unset")}>Cookie settings</button>;
}
