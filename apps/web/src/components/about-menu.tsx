"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { FlatIcon } from "@/components/flat-icons";

const links = [
  ["Explore Civitas", "/about/app"],
  ["Why It Is Needed", "/about/why"],
  ["Engineering Team", "/about/developers"],
] as const;

export function AboutMenu({ isActive = false }: { isActive?: boolean }) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const close = (event: MouseEvent) => {
      if (!ref.current?.contains(event.target as Node)) setOpen(false);
    };
    const escape = (event: KeyboardEvent) => {
      if (event.key === "Escape") setOpen(false);
    };
    document.addEventListener("mousedown", close);
    document.addEventListener("keydown", escape);
    return () => {
      document.removeEventListener("mousedown", close);
      document.removeEventListener("keydown", escape);
    };
  }, []);

  return (
    <div className={`aboutmenu-controlled ${isActive ? "active" : ""}`} ref={ref}>
      <button
        className={`about-trigger ${isActive ? "active" : ""}`}
        aria-expanded={open}
        aria-haspopup="menu"
        onClick={() => setOpen((value) => !value)}
      >
        <span>Explore</span>
        <FlatIcon name="chevron-down" size={14} className={`menu-chevron ${open ? "open" : ""}`} />
      </button>
      {open && (
        <div className="about-popover" role="menu">
          <p className="popover-kicker">EXPLORE CIVITAS</p>
          {links.map(([label, href]) => (
            <Link
              role="menuitem"
              key={href}
              href={href}
              onClick={() => setOpen(false)}
            >
              {label}
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
