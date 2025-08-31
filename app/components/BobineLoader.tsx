"use client";
import React from "react";

/**
 * BobineLoader — animated loader inspired by the provided artwork
 * Drop into any Next.js (App Router or Pages) project.
 *
 * Props
 * - size: overall px size (default 240)
 * - speed: animation speed multiplier (default 1)
 * - accent: highlight color (default #E8FF66)
 * - stroke: line color (default #0A0A0A)
 * - bg: optional background color ("transparent" by default)
 */
export default function BobineLoader({
  size = 320,
  speed = 1,
  accent = "#E8FF66",
  stroke = "#0A0A0A",
  bg = "transparent",
}: {
  size?: number;
  speed?: number;
  accent?: string;
  stroke?: string;
  bg?: string;
}) {
  const s = size;

  return (
    <div
      aria-label="Chargement"
      role="status"
      style={{ width: s, height: s, display: "inline-block", background: bg }}
      className="relative"
    >
      <svg
        viewBox="0 0 320 320"
        width={s}
        height={s}
        xmlns="http://www.w3.org/2000/svg"
      >
        {/* --- defs & masks --- */}
        <defs>
          <linearGradient id="tubeShine" x1="0" x2="0" y1="0" y2="1">
            <stop offset="0%" stopColor="#ffffff" stopOpacity="0.25" />
            <stop offset="100%" stopColor="#ffffff" stopOpacity="0.1" />
          </linearGradient>

          {/* mask to keep particles & coils inside the tube */}
          <mask id="tubeMask">
            <rect x="0" y="0" width="320" height="320" fill="black" />
            <rect x="116" y="38" width="88" height="244" rx="12" fill="white" />
          </mask>

          {/* ring path for repeated coil ellipses */}
          <ellipse id="coilEllipse" cx="160" cy="170" rx="120" ry="34" />

          <style>{`
            @keyframes floatParticles { 0% { transform: translateY(24px); } 50% { transform: translateY(-18px); } 100% { transform: translateY(24px); } }
            @keyframes rotateDisc { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
            @keyframes sweepDash { from { stroke-dashoffset: 0; } to { stroke-dashoffset: -240; } }
            .a { animation-duration: ${6 / speed}s; animation-iteration-count: infinite; animation-timing-function: ease-in-out; }
            .rot { animation: rotateDisc ${18 / speed}s linear infinite; transform-origin: 270px 70px; }
            .rot2 { animation: rotateDisc ${14 / speed}s linear infinite; transform-origin: 90px 250px; }
            .float { animation: floatParticles ${3.8 / speed}s ease-in-out infinite; }
            .dash { stroke-dasharray: 12 10; animation: sweepDash ${2.4 / speed}s linear infinite; }
          `}</style>
        </defs>

        {/* --- lemon circles/triangles in the back --- */}
        <g opacity="0.65">
          <circle className="rot" cx="270" cy="70" r="86" fill={accent} />
        </g>
        <g opacity="0.9">
          <polygon className="rot2" points="20,260 140,200 180,310" fill={accent} />
        </g>

        {/* --- coil wires (outside mask to show full rings) --- */}
        <g stroke={stroke} fill="none" strokeWidth="6" opacity="0.95">
          {Array.from({ length: 9 }).map((_, i) => (
            <use
              key={i}
              href="#coilEllipse"
              transform={`translate(0 ${-72 + i * 18})`}
              className="dash"
            />
          ))}
        </g>

        {/* --- tube (masked content) --- */}
        <g mask="url(#tubeMask)">
          {/* tube body */}
          <rect x="116" y="38" width="88" height="244" rx="12" fill="url(#tubeShine)" />
          <rect x="116" y="38" width="88" height="244" rx="12" fill="none" stroke={stroke} strokeWidth="6" />

          {/* top & bottom rims to mimic perspective */}
          <ellipse cx="160" cy="38" rx="44" ry="12" fill="none" stroke={stroke} strokeWidth="6" />
          <ellipse cx="160" cy="282" rx="44" ry="12" fill="none" stroke={stroke} strokeWidth="6" />

          {/* label "bobine" */}
          <text x="201" y="140" transform="rotate(-90 201 140)" fontFamily="ui-sans-serif, system-ui, Arial" fontWeight={700} fontSize="18" fill={stroke}>
            bobine
          </text>

          {/* particles (white with accent highlights), floating as a group */}
          <g className="a float">
            {createParticles().map((p, idx) => (
              <circle key={idx} cx={p[0]} cy={p[1]} r={p[2]} fill={idx % 5 === 0 ? accent : "#ffffff"} stroke={stroke} strokeWidth="3" />
            ))}
          </g>
        </g>
      </svg>
      <span className="sr-only">Chargement…</span>
    </div>
  );
}

// Static particle field (roughly matching the composition of the reference) — tuned to sit inside the coil region
function createParticles(): [number, number, number][] {
  const pts: [number, number, number][] = [];
  const seed = 42;
  let x = seed;
  // simple deterministic PRNG for consistent layout
  const rand = () => (x = (x * 1664525 + 1013904223) % 4294967296) / 4294967296;
  for (let i = 0; i < 70; i++) {
    const px = 132 + rand() * 56; // within tube width
    const py = 110 + rand() * 108; // within coil height
    const r = 6 + rand() * 2.2;
    pts.push([px, py, r]);
  }
  return pts;
}
