"use client";
import React, { useState, useEffect, useId, useRef, useCallback } from "react";
import { Upload } from "lucide-react";
import { useFileDrop } from "@/src/contexts/FileDropContext";
import { isTauriEnv } from "@/src/lib/utils/tauriHelpers";
import { useTauriDragDrop } from "@/src/hooks/useTauriDragDrop";
import DragOverlay from "./DragOverlay";
import FileList from "./FileList";
import UploadZoneError from "./UploadZoneError";

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
  const zoneId = useId();
  const { activeZoneId, setActiveZoneId, registerZone, unregisterZone } = useFileDrop();
  const [isDragOver, setIsDragOver] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const dropZoneRef = useRef<HTMLDivElement>(null);
  const dragCounterRef = useRef(0);
  const activeZoneIdRef = useRef<string | null>(null);

  const isAtLimit = selectedFiles.length >= maxFiles;
  const remainingSlots = maxFiles - selectedFiles.length;

  // Sync activeZoneId with ref
  useEffect(() => {
    activeZoneIdRef.current = activeZoneId;
  }, [activeZoneId]);

  const handleNewFiles = useCallback((newFiles: File[]) => {
    setErrorMessage("");
    if (selectedFiles.length + newFiles.length > maxFiles) {
      setErrorMessage(`Limite dépassée ! Maximum ${maxFiles} fichier(s) par zone.`);
      return;
    }
    onFileSelect([...selectedFiles, ...newFiles]);
  }, [selectedFiles, maxFiles, onFileSelect]);

  const removeFile = useCallback((indexToRemove: number) => {
    const updatedFiles = selectedFiles.filter((_, index) => index !== indexToRemove);
    onFileSelect(updatedFiles);
    setErrorMessage("");
  }, [selectedFiles, onFileSelect]);

  const resetDragState = useCallback(() => {
    setIsDragOver(false);
    setActiveZoneId(null);
    activeZoneIdRef.current = null;
    dragCounterRef.current = 0;
  }, [setActiveZoneId]);

  // Register zone element
  useEffect(() => {
    if (dropZoneRef.current) {
      registerZone(zoneId, dropZoneRef.current);
    }
    return () => {
      unregisterZone(zoneId);
    };
  }, [zoneId, registerZone, unregisterZone]);

  // Setup Tauri drag-and-drop listeners
  useTauriDragDrop({
    zoneId,
    description,
    isAtLimit,
    dropZoneRef,
    activeZoneIdRef,
    dragCounterRef,
    setIsDragOver,
    setActiveZoneId,
    handleNewFiles,
    resetDragState,
    onError: setErrorMessage,
  });

  return (
    <div className="space-y-4">
      {!isAtLimit && (
        <div className="relative" style={{ isolation: 'isolate' }}>
          {isDragOver && <DragOverlay />}

          <div
            ref={dropZoneRef}
            className={`
              relative border-2 p-6 rounded-lg flex flex-col items-center justify-center
              transition-all duration-300 ease-out bg-background
              ${isDragOver
                ? "border-transparent"
                : "border-dashed border-border hover:border-primary/30"
              }
              hover:bg-muted/30 cursor-pointer group
            `}
            style={{ zIndex: 0 }}
          >
            <label
              className="cursor-pointer flex flex-col justify-center items-center w-full"
              onDragEnter={(e) => {
                e.preventDefault();
                e.stopPropagation();
                if (!isTauriEnv()) {
                  dragCounterRef.current++;
                  if (dragCounterRef.current === 1 && !isAtLimit) {
                    setIsDragOver(true);
                    setActiveZoneId(zoneId);
                  }
                }
              }}
              onDragOver={(e) => {
                e.preventDefault();
                e.stopPropagation();
              }}
              onDragLeave={(e) => {
                e.preventDefault();
                e.stopPropagation();
                if (!isTauriEnv()) {
                  dragCounterRef.current--;
                  if (dragCounterRef.current === 0) {
                    setIsDragOver(false);
                    setActiveZoneId(null);
                  }
                }
              }}
              onDrop={(e) => {
                e.preventDefault();
                e.stopPropagation();

                if (!isTauriEnv()) {
                  dragCounterRef.current = 0;
                  setIsDragOver(false);

                  if (e.dataTransfer.files?.length) {
                    handleNewFiles(Array.from(e.dataTransfer.files));
                    setActiveZoneId(null);
                  }
                }
              }}
            >
              <p className="mb-4 text-center font-medium text-foreground">
                {description}
              </p>

              <div className="flex items-center space-x-4 mb-4">
                <div className="p-3 rounded-lg bg-secondary">
                  <Upload
                    className={`text-secondary-foreground ${
                      isDragOver ? "animate-bounce-smooth" : "group-hover-bounce-smooth"
                    }`}
                    size={24}
                  />
                </div>

                <div className="text-sm">
                  <div className="font-semibold text-foreground">
                    {selectedFiles.length} / {maxFiles} fichier(s)
                  </div>
                  <div className="text-muted-foreground text-xs">
                    {remainingSlots} restant(s)
                  </div>
                </div>
              </div>

              <input
                type="file"
                multiple={maxFiles > 1}
                className="hidden"
                onChange={(e) => handleNewFiles(Array.from(e.target.files || []))}
                aria-label={description}
              />

              <p className="text-sm text-muted-foreground">
                Glissez-déposez vos fichiers ou cliquez pour parcourir
              </p>
            </label>
          </div>
        </div>
      )}

      <FileList
        files={selectedFiles}
        description={description}
        maxFiles={maxFiles}
        onRemoveFile={removeFile}
      />

      <UploadZoneError message={errorMessage} />
    </div>
  );
}
