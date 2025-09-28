"use client";

import React from "react";
import { Loader2 } from "lucide-react";
import { cn } from "@/src/lib/utils";

type SimpleLoaderProps = {
  open: boolean;
  message?: string;
  className?: string;
};

export default function SimpleLoader({
  open,
  message = "Navigation en cours...",
  className,
}: SimpleLoaderProps) {
  if (!open) return null;

  return (
    <div
      className={cn(
        "fixed inset-0 z-[100] flex items-center justify-center",
        "bg-black/30 backdrop-blur-sm"
      )}
      role="presentation"
      aria-hidden={!open}
    >
      <div
        className={cn(
          "flex flex-col items-center space-y-4 p-8 bg-white dark:bg-zinc-900/90 rounded-2xl shadow-2xl border border-white/10",
          className
        )}
        role="status"
        aria-live="polite"
      >
        <Loader2 className="h-8 w-8 animate-spin text-secondary" />
        <p className="text-sm text-muted-foreground animate-pulse">
          {message}
        </p>
      </div>
    </div>
  );
}