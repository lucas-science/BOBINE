"use client";

import React, { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/src/components/ui/dialog";
import { Button } from "@/src/ui/button";
import { Badge } from "@/src/components/ui/badge";
import { copyErrorToClipboard, ErrorDetails } from "@/src/lib/utils/errorFormatter";
import { toast } from "sonner";

interface ErrorDebugDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  errorDetails: ErrorDetails | null;
}

/**
 * ErrorDebugDialog - Development-only error debugging dialog
 *
 * Displays detailed error information including:
 * - Frontend error message and stack trace
 * - Backend error (Python/Rust) if available
 * - Copy to clipboard functionality
 *
 * Only renders in development mode (process.env.NODE_ENV === 'development')
 */
export function ErrorDebugDialog({
  open,
  onOpenChange,
  errorDetails,
}: ErrorDebugDialogProps) {
  const [isCopying, setIsCopying] = useState(false);

  // Only render in development mode
  if (process.env.NODE_ENV !== "development") {
    return null;
  }

  if (!errorDetails) {
    return null;
  }

  const handleCopyToClipboard = async () => {
    setIsCopying(true);
    const success = await copyErrorToClipboard(errorDetails);

    if (success) {
      toast.success("Erreur copiée dans le presse-papiers");
    } else {
      toast.error("Échec de la copie dans le presse-papiers");
    }

    setIsCopying(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <div className="flex items-center gap-2 mb-2">
            <DialogTitle className="text-xl font-bold text-red-600">
              🐛 Error Debug Info
            </DialogTitle>
            <Badge variant="destructive" className="ml-auto">
              DEV MODE ONLY
            </Badge>
          </div>
          <DialogDescription className="text-left">
            Informations détaillées pour le débogage. Cet écran n&apos;apparaît qu&apos;en mode développement.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 mt-4">
          <div className="text-xs text-muted-foreground">
            <span className="font-semibold">Timestamp:</span> {errorDetails.timestamp}
          </div>

          <div className="p-4 border border-red-200 bg-red-50 rounded-lg shadow-sm">
            <h3 className="text-sm font-semibold text-red-800 mb-2 flex items-center gap-2">
              <span className="text-lg">⚠️</span>
              Frontend Error
            </h3>
            <div className="space-y-3">
              <div>
                <p className="text-xs text-red-700 font-semibold mb-1">Message:</p>
                <pre className="text-xs bg-white p-3 rounded border border-red-200 overflow-x-auto">
                  {errorDetails.message}
                </pre>
              </div>

              {errorDetails.stack && (
                <div>
                  <p className="text-xs text-red-700 font-semibold mb-1">Stack Trace:</p>
                  <pre className="text-xs bg-white p-3 rounded border border-red-200 overflow-x-auto max-h-60 overflow-y-auto">
                    {errorDetails.stack}
                  </pre>
                </div>
              )}
            </div>
          </div>

          {errorDetails.backendError && (
            <div className="p-4 border border-orange-200 bg-orange-50 rounded-lg shadow-sm">
              <h3 className="text-sm font-semibold text-orange-800 mb-2 flex items-center gap-2">
                <span className="text-lg">🔧</span>
                Backend Error (Python/Rust)
              </h3>
              <pre className="text-xs bg-white p-3 rounded border border-orange-200 overflow-x-auto max-h-60 overflow-y-auto">
                {errorDetails.backendError}
              </pre>
            </div>
          )}

          {errorDetails.rawError && (
            <details className="text-xs">
              <summary className="cursor-pointer text-muted-foreground hover:text-foreground font-semibold">
                Raw Error Object (click to expand)
              </summary>
              <pre className="mt-2 bg-muted p-3 rounded border overflow-x-auto max-h-40 overflow-y-auto">
                {JSON.stringify(errorDetails.rawError, null, 2)}
              </pre>
            </details>
          )}
        </div>

        <div className="flex gap-2 mt-6">
          <Button
            onClick={handleCopyToClipboard}
            disabled={isCopying}
            variant="outline"
            className="flex-1 cursor-pointer"
          >
            {isCopying ? "Copie en cours..." : "📋 Copier dans le presse-papiers"}
          </Button>
          <Button
            onClick={() => onOpenChange(false)}
            className="flex-1 cursor-pointer"
          >
            Fermer
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
