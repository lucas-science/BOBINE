"use client";
import React, { useState } from "react";
import { Upload } from "lucide-react";

export interface FileUploadZoneProps {
  description: string;
  onFileSelect: (files: File[]) => void;
  selectedFiles: File[];
  maxFiles: number;
}

export default function FileUploadZone({
  description,
  onFileSelect,
  selectedFiles,
  maxFiles,
}: FileUploadZoneProps) {
  const [isDragOver, setIsDragOver] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  const isAtLimit = selectedFiles.length >= maxFiles;
  const remainingSlots = maxFiles - selectedFiles.length;

  const handleNewFiles = (newFiles: File[]) => {
    setErrorMessage("");
    if (selectedFiles.length + newFiles.length > maxFiles) {
      setErrorMessage(`Limite dépassée ! Maximum ${maxFiles} fichier(s) par zone.`);
      return;
    }
    onFileSelect([...selectedFiles, ...newFiles]);
  };

  return (
    <div className="space-y-3">
      <div
        className={[
          "border-2 border-dashed p-4 rounded-lg flex flex-col items-center justify-center transition-all duration-200",
          isDragOver ? "border-blue-400 bg-blue-50" : "border-gray-300",
          isAtLimit ? "bg-gray-50 opacity-60" : "bg-gray-50 hover:bg-gray-100",
        ].join(" ")}
        onDragOver={(e) => { e.preventDefault(); setIsDragOver(true); }}
        onDragLeave={(e) => { e.preventDefault(); setIsDragOver(false); }}
        onDrop={(e) => {
          e.preventDefault(); setIsDragOver(false);
          handleNewFiles(Array.from(e.dataTransfer.files || []));
        }}
      >
        <label className={`cursor-pointer flex flex-col justify-center items-center w-full ${isAtLimit ? "cursor-not-allowed" : ""}`}>
          <p className="text-gray-600 mb-4 text-center">{description}</p>

          <div className="flex items-center space-x-4 mb-3">
            <div className={`p-2 rounded-lg transition-colors ${isAtLimit ? "bg-gray-400" : "bg-blue-500 hover:bg-blue-600"}`}>
              <Upload className="text-white" size={20} />
            </div>

            <div className="text-sm">
              <div className={`font-medium ${isAtLimit ? "text-red-600" : "text-gray-700"}`}>
                {selectedFiles.length} / {maxFiles} fichier(s)
              </div>
              <div className="text-gray-500 text-xs">
                {isAtLimit ? "Limite atteinte" : `${remainingSlots} restant(s)`}
              </div>
            </div>
          </div>

          <input
            type="file"
            multiple={maxFiles > 1}
            className="hidden"
            disabled={isAtLimit}
            onChange={(e) => handleNewFiles(Array.from(e.target.files || []))}
          />

          <p className={`text-sm ${isAtLimit ? "text-gray-400" : "text-gray-500"}`}>
            {isAtLimit ? "Limite atteinte" : "Drag and drop or click to upload"}
          </p>
        </label>
      </div>

      {!!errorMessage && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-3">
          <div className="flex items-center">
            <span className="text-red-400">⚠️</span>
            <p className="text-sm text-red-700 ml-3">{errorMessage}</p>
          </div>
        </div>
      )}
    </div>
  );
}
