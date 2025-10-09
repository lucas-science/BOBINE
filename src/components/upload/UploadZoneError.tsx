import React from "react";

interface UploadZoneErrorProps {
  message: string;
}

/**
 * Error message for upload zone
 */
export default function UploadZoneError({ message }: UploadZoneErrorProps) {
  if (!message) return null;

  return (
    <div className="bg-destructive/10 border border-destructive/20 rounded-lg p-3">
      <div className="flex items-center">
        <span className="text-destructive">⚠️</span>
        <p className="text-sm text-destructive ml-3">{message}</p>
      </div>
    </div>
  );
}
