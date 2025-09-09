import React from "react";
import { Loader2 } from "lucide-react";

export default function SelectLoading() {
  return (
    <div className="flex items-center justify-center h-full w-full">
      <div className="flex flex-col items-center space-y-4">
        <Loader2 className="h-8 w-8 animate-spin text-secondary" />
        <p className="text-sm text-muted-foreground animate-pulse">
          Chargement...
        </p>
      </div>
    </div>
  );
}