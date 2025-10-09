import React from "react";

/**
 * Animated overlay displayed when dragging files over a drop zone
 */
export default function DragOverlay() {
  return (
    <>
      {/* Primary glow - moving gradient */}
      <div
        className="absolute inset-0 rounded-lg pointer-events-none"
        style={{
          background: 'linear-gradient(135deg, rgba(227, 234, 45, 0.3), rgba(59, 130, 246, 0.25), rgba(227, 234, 45, 0.3), rgba(59, 130, 246, 0.25))',
          backgroundSize: '400% 400%',
          animation: 'glowMove 4s ease-in-out infinite, glowPulse 2s ease-in-out infinite',
          zIndex: 1,
        }}
      />

      {/* Secondary glow - blue accent pulse */}
      <div
        className="absolute inset-0 rounded-lg pointer-events-none"
        style={{
          background: 'radial-gradient(ellipse at center, rgba(59, 130, 246, 0.2), rgba(227, 234, 45, 0.15), transparent 70%)',
          animation: 'glowPulse 3s ease-in-out infinite 0.5s',
          zIndex: 1,
        }}
      />

      {/* Animated dashed border */}
      <svg
        className="absolute inset-0 pointer-events-none"
        width="100%"
        height="100%"
        style={{ zIndex: 2 }}
      >
        <rect
          x="2"
          y="2"
          width="calc(100% - 4px)"
          height="calc(100% - 4px)"
          rx="8"
          fill="none"
          stroke="hsl(211, 100%, 57%)"
          strokeWidth="3"
          strokeDasharray="12 8"
          strokeDashoffset="0"
          style={{
            animation: 'dashedRotate 20s linear infinite',
          }}
        />
      </svg>
    </>
  );
}
