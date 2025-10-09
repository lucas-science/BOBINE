"use client";
import React, { useState, useEffect, useId, useRef, useCallback } from "react";
import { Upload } from "lucide-react";
import { useFileDrop } from "@/src/contexts/FileDropContext";
import { getCurrentWebviewWindow } from "@tauri-apps/api/webviewWindow";
import { pathsToFiles } from "@/src/lib/fileUtils";
import { isTauriEnv, checkPositionOver } from "@/src/lib/utils/tauriHelpers";
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

  // Setup Tauri file drop listeners
  useEffect(() => {
    let unlistenDrop: (() => void) | undefined;
    let isMounted = true;
    let isListenerRegistered = false;

    const setupListeners = async () => {
      try {
        if (!isTauriEnv()) return;

        const appWebview = getCurrentWebviewWindow();
        if (!appWebview) return;

        const unlisten = await appWebview.onDragDropEvent(async (event) => {
          if (!isMounted) return;

          const payload = event.payload as {
            type: string;
            position?: { x: number; y: number };
            paths?: string[];
          };
          const { type, position, paths } = payload;

          if (type === "enter" || type === "over") {
            if (dropZoneRef.current && position) {
              const rect = dropZoneRef.current.getBoundingClientRect();
              const isOver = checkPositionOver(rect, position);

              if (isOver && !isAtLimit) {
                setIsDragOver(true);
                setActiveZoneId(zoneId);
                activeZoneIdRef.current = zoneId;
                dragCounterRef.current = 1;
              } else if (activeZoneIdRef.current === zoneId && !isOver) {
                resetDragState();
              }
            }
          } else if (type === "drop") {
            if (activeZoneIdRef.current === zoneId && paths?.length) {
              try {
                const files = await pathsToFiles(paths);
                handleNewFiles(files);
              } catch (error) {
                console.error(`[FileUploadZone ${description}] Error converting files:`, error);
                setErrorMessage("Erreur lors de la lecture des fichiers.");
              }
            }
            resetDragState();
          } else if (type === "leave") {
            if (activeZoneIdRef.current === zoneId) {
              resetDragState();
            }
          } else if (type === "cancel") {
            resetDragState();
          }
        });

        if (unlisten && typeof unlisten === 'function' && isMounted) {
          unlistenDrop = unlisten;
          isListenerRegistered = true;
        } else if (unlisten) {
          unlisten();
        }
      } catch (error) {
        console.error(`[FileUploadZone ${description}] Failed to setup Tauri listeners:`, error);
      }
    };

    setupListeners();

    return () => {
      isMounted = false;

      if (isListenerRegistered && unlistenDrop) {
        const isDev = process.env.NODE_ENV === 'development';
        if (isDev) return;

        setTimeout(() => {
          try {
            if (typeof unlistenDrop === 'function' && isTauriEnv()) {
              unlistenDrop();
            }
          } catch {
            // Silently ignore cleanup errors
          }
        }, 0);
      }
    };
  }, [description, zoneId, isAtLimit, handleNewFiles, resetDragState, setActiveZoneId]);

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
