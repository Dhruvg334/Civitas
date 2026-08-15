"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";

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
        type="button"
        className={`about-trigger ${isActive ? "active" : ""} ${open ? "menu-open" : ""}`}
        aria-expanded={open}
        aria-haspopup="menu"
        onClick={() => setOpen((value) => !value)}
      >
        Explore
      </button>
      {open && (
        <div className="about-popover animated-popover" role="menu">
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

      <style jsx>{`
        .aboutmenu-controlled {
          position: relative;
          display: inline-flex;
          align-items: center;
        }
        .about-trigger {
          height: 38px;
          padding: 0 14px;
          border: 0;
          background: transparent;
          font-size: 0.82rem;
          font-weight: 750;
          color: #172019;
          border-radius: 4px;
          cursor: pointer;
          transition: all 0.15s ease;
          display: inline-flex;
          align-items: center;
          justify-content: center;
        }
        .about-trigger:hover,
        .about-trigger.menu-open,
        .about-trigger.active {
          background: #172019;
          color: #ffffff;
        }
        .about-popover {
          position: absolute;
          top: calc(100% + 8px);
          left: 0;
          width: 230px;
          background: #ffffff;
          border: 2px solid #172019;
          box-shadow: 4px 4px 0 #172019;
          padding: 8px;
          z-index: 100;
          display: flex;
          flex-direction: column;
          border-radius: 4px;
        }
        .animated-popover {
          animation: popoverSlide 0.2s cubic-bezier(0.16, 1, 0.3, 1) forwards;
          transform-origin: top left;
        }
        @keyframes popoverSlide {
          from {
            opacity: 0;
            transform: translateY(-6px) scale(0.97);
          }
          to {
            opacity: 1;
            transform: translateY(0) scale(1);
          }
        }
        .popover-kicker {
          margin: 4px 8px 6px;
          color: #0f5f4f;
          font-size: 0.62rem;
          font-weight: 900;
          letter-spacing: 0.12em;
        }
        .about-popover :global(a) {
          padding: 10px 10px;
          font-size: 0.82rem;
          font-weight: 750;
          color: #172019;
          text-decoration: none;
          border-radius: 3px;
          transition: background 0.12s ease, color 0.12s ease;
          border-top: 1px solid #f0ecdf;
        }
        .about-popover :global(a:first-of-type) {
          border-top: 0;
        }
        .about-popover :global(a:hover) {
          background: #fbf9f4;
          color: #e84d7a;
          padding-left: 14px;
        }
      `}</style>
    </div>
  );
}
