// app/components/LoaderOverlay.tsx
"use client";

import * as React from "react";
import { Card, CardContent } from "@/src/components/ui/card";
import { Progress } from "@/src/components/ui/progress";
import { motion, useMotionValue, useAnimationFrame } from "framer-motion";
import { cn } from "@/src/lib/utils";

type LoaderOverlayProps = {
  open: boolean;
  currentStep: number;   // e.g., 1
  totalSteps: number;    // e.g., 4
  currentTask: string;   // e.g., "copie des fichiers…"
  className?: string;
};

export default function LoaderOverlay({
  open,
  currentStep,
  totalSteps,
  currentTask,
  className,
}: LoaderOverlayProps) {
  if (!open) return null;

  const pct =
    totalSteps > 0 ? Math.min(100, Math.max(0, (currentStep / totalSteps) * 100)) : 0;

  return (
    <div
      className={cn(
        "fixed inset-0 z-[100] flex items-center justify-center",
        "bg-black/30 backdrop-blur-sm"
      )}
      role="presentation"
      aria-hidden={!open}
    >
      <Card
        className={cn(
          "w-[min(92vw,420px)] rounded-2xl shadow-2xl border border-white/10",
          "bg-white/90 dark:bg-zinc-900/90"
        )}
        role="status"
        aria-live="polite"
      >
        <CardContent className="p-6">
          {/* Fancy geometric animation */}
          <div className="mx-auto mb-5 flex items-center justify-center">
            <GeometricLoader />
          </div>

          {/* Step indicator */}
          <div className="mb-2 text-center text-sm font-medium text-zinc-700 dark:text-zinc-300">
            Étape {currentStep} / {totalSteps}
          </div>

          {/* Current task */}
          <div className="mb-4 text-center text-sm text-zinc-500 dark:text-zinc-400">
            {currentTask}
          </div>

          {/* Progress bar */}
          <Progress value={pct} className="h-2" aria-label="progression" />

          {/* Subtle hint */}
          <div className="mt-3 text-center text-[11px] text-zinc-400">
            Merci de patienter…
          </div>
        </CardContent>
      </Card>
    </div>
  );
}


function GeometricLoader() {
  // centre et rayon d’orbite
  const W = 144; // 36 * 4 (taille du conteneur)
  const H = 144;

  // positions animées (MotionValue pour perf + subpixel)
  const x1 = useMotionValue(0), y1 = useMotionValue(0), r1 = useMotionValue(0);
  const x2 = useMotionValue(0), y2 = useMotionValue(0), r2 = useMotionValue(0);
  const x3 = useMotionValue(0), y3 = useMotionValue(0), r3 = useMotionValue(0), s3 = useMotionValue(1);

  // horloge
  useAnimationFrame((t) => {
    // t en ms -> secondes
    const ts = t / 1000;

    // trajectoires lissées (Lissajous + légers déphasages irrationnels pour éviter toute répétition courte)
    // Shape 1 (cercle)
    const a1 = 26, b1 = 22, w1 = 0.9, w1y = 1.13, rot1 = 0.35;
    x1.set(W/2 + a1 * Math.sin(w1 * ts + Math.PI / 6));
    y1.set(H/2 + b1 * Math.sin(w1y * ts));
    r1.set((ts * rot1 * 360) % 360);

    // Shape 2 (carré)
    const a2 = 34, b2 = 18, w2 = 1.27, w2y = 0.85, rot2 = -0.55;
    x2.set(W/2 + a2 * Math.cos(w2 * ts + Math.PI / 3));
    y2.set(H/2 + b2 * Math.sin(w2y * ts + Math.PI / 8));
    r2.set((ts * rot2 * 360) % 360);

    // Shape 3 (triangle)
    const a3 = 20, b3 = 32, w3 = 1.07, w3y = 1.41, rot3 = 0.8;
    x3.set(W/2 + a3 * Math.sin(w3 * ts + Math.PI / 5));
    y3.set(H/2 + b3 * Math.cos(w3y * ts + Math.PI / 9));
    r3.set((ts * rot3 * 360) % 360);

    // petit “respir” sur le triangle (scale) pour de la vie
    s3.set(1 + 0.05 * Math.sin(ts * 1.2));
  });

  return (
    <div
      className="relative h-36 w-36 rounded-2xl overflow-hidden"
      style={{
        // fond doux
        background:
          "linear-gradient(135deg, rgba(250,250,250,0.9), rgba(244,244,245,0.9))",
      }}
    >
      {/* Glow subtil */}
      <div className="pointer-events-none absolute inset-0 rounded-2xl blur-2xl opacity-70 bg-gradient-to-tr from-blue-200/40 via-cyan-200/30 to-fuchsia-200/30 dark:from-blue-400/10 dark:via-cyan-400/10 dark:to-fuchsia-400/10" />

      {/* Orbite décorative en rotation lente, continue */}
      <motion.div
        className="absolute inset-2 rounded-[1.25rem] border border-zinc-200/70 dark:border-zinc-700/60"
        animate={{ rotate: 360 }}
        transition={{ duration: 24, repeat: Infinity, ease: "linear" }}
        style={{ willChange: "transform" }}
      />

      {/* Cercle */}
      <motion.div
        className="absolute"
        style={{
          left: 0,
          top: 0,
          x: x1,
          y: y1,
          rotate: r1,
          willChange: "transform",
          width: 24,
          height: 24,
          marginLeft: -12,
          marginTop: -12,
        }}
      >
        <div className="h-full w-full rounded-full bg-gradient-to-br from-sky-400 to-cyan-500 shadow-lg shadow-sky-400/30" />
      </motion.div>

      {/* Carré */}
      <motion.div
        className="absolute"
        style={{
          left: 0,
          top: 0,
          x: x2,
          y: y2,
          rotate: r2,
          willChange: "transform",
          width: 22,
          height: 22,
          marginLeft: -11,
          marginTop: -11,
        }}
      >
        <div className="h-full w-full rounded-xl bg-gradient-to-br from-fuchsia-500 to-pink-500 shadow-lg shadow-pink-400/30" />
      </motion.div>

      {/* Triangle */}
      <motion.div
        className="absolute"
        style={{
          left: 0,
          top: 0,
          x: x3,
          y: y3,
          rotate: r3,
          scale: s3,
          willChange: "transform",
          width: 0,
          height: 0,
          marginLeft: -12,
          marginTop: -10,
        }}
      >
        {/* triangle via border */}
        <div
          className="shadow-lg"
          style={{
            width: 0,
            height: 0,
            borderLeft: "12px solid transparent",
            borderRight: "12px solid transparent",
            borderBottom: "20px solid rgb(34 197 94)", // green-500
            filter: "drop-shadow(0 8px 14px rgba(34,197,94,0.35))",
          }}
        />
      </motion.div>
    </div>
  );
}
