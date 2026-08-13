"use client";

import { useState } from "react";

export function LocationRequest() {
  const [message, setMessage] = useState("Location is optional. You can enter coordinates or a nearby landmark instead.");
  const request = () => {
    if (!navigator.geolocation) { setMessage("This browser does not support location. Add a landmark or coordinates instead."); return; }
    navigator.geolocation.getCurrentPosition(({ coords }) => setMessage(`Approximate location ready: ${coords.latitude.toFixed(4)}, ${coords.longitude.toFixed(4)}. Review it before submitting.`), () => setMessage("Location was not shared. You can continue with a landmark or coordinates."), { enableHighAccuracy: false, timeout: 10_000, maximumAge: 300_000 });
  };
  return <div className="location-request"><div><b>Share approximate location</b><p>{message}</p></div><button type="button" className="outline" onClick={request}>Use my location</button></div>;
}
