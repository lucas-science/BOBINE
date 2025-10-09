"use client";
import React, { useState, useEffect, useId, useRef } from "react";
import { Upload, X, File, FileText, FileImage, FileVideo } from "lucide-react";
import { useFileDrop } from "@/src/contexts/FileDropContext";
import { getCurrentWebviewWindow } from "@tauri-apps/api/webviewWindow";
import { pathsToFiles } from "@/src/lib/fileUtils";

export interface FileUploadZoneProps {
  description: string;
  onFileSelect: (files: File[]) => void;
  selectedFiles: File[];
  maxFiles: number;
}

// Utilitaires
const getFileIcon = (file: File) => {
  const type = file.type.toLowerCase();
  if (type.startsWith('image/')) return FileImage;
  if (type.startsWith('video/')) return FileVideo;
  if (type.includes('text') || type.includes('document')) return FileText;
  return File;
};

const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
};

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

  // Log component mount
  useEffect(() => {
    console.log(`[FileUploadZone ${description}] Component mounted with zoneId: ${zoneId}`);

    // More detailed Tauri detection
    const isTauri = typeof window !== 'undefined' && !!(window as any).__TAURI_INTERNALS__;
    const hasTauriWindow = typeof getCurrentWebviewWindow === 'function';

    console.log(`[FileUploadZone ${description}] Tauri environment:`, {
      __TAURI__: !!(window as any).__TAURI__,
      __TAURI_INTERNALS__: !!(window as any).__TAURI_INTERNALS__,
      hasTauriWindow,
      isTauri,
      userAgent: navigator.userAgent
    });

    return () => {
      console.log(`[FileUploadZone ${description}] Component unmounting`);
    };
  }, [description, zoneId]);

  // Keep activeZoneId in sync with ref
  useEffect(() => {
    activeZoneIdRef.current = activeZoneId;
  }, [activeZoneId]);

  const handleNewFiles = (newFiles: File[]) => {
    console.log(`[FileUploadZone ${description}] handleNewFiles called with ${newFiles.length} files`);
    setErrorMessage("");
    if (selectedFiles.length + newFiles.length > maxFiles) {
      setErrorMessage(`Limite dépassée ! Maximum ${maxFiles} fichier(s) par zone.`);
      return;
    }
    onFileSelect([...selectedFiles, ...newFiles]);
  };

  const removeFile = (indexToRemove: number) => {
    const updatedFiles = selectedFiles.filter((_, index) => index !== indexToRemove);
    onFileSelect(updatedFiles);
    setErrorMessage("");
  };

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
        // Check if we're in Tauri environment (Tauri 2.x uses __TAURI_INTERNALS__)
        const isTauriEnv = typeof window !== 'undefined' &&
                          ((window as any).__TAURI_INTERNALS__ || (window as any).__TAURI__);

        if (!isTauriEnv) {
          console.log(`[FileUploadZone ${description}] Not in Tauri environment, skipping Tauri listeners`);
          return;
        }

        console.log(`[FileUploadZone ${description}] ✅ Tauri environment detected!`);

        const appWebview = getCurrentWebviewWindow();
        if (!appWebview) {
          console.warn(`[FileUploadZone ${description}] Could not get current webview`);
          return;
        }

        console.log(`[FileUploadZone ${description}] Setting up Tauri drag-drop listeners (zoneId: ${zoneId})`);

        // Listen for drag and drop events
        const unlisten = await appWebview.onDragDropEvent(async (event) => {
          if (!isMounted) return;

          console.log(`[FileUploadZone ${description}] Tauri event:`, event.payload.type, {
            position: event.payload.position,
            paths: event.payload.paths,
            zoneId,
            activeZoneId: activeZoneIdRef.current,
            isAtLimit
          });

          if (event.payload.type === "enter" || event.payload.type === "over") {
            // Check if cursor is over this zone using position
            if (dropZoneRef.current && event.payload.position) {
              const rect = dropZoneRef.current.getBoundingClientRect();

              // Try WITHOUT dividing by DPR first - Tauri may already provide logical coordinates
              let x = event.payload.position.x;
              let y = event.payload.position.y;

              console.log(`[FileUploadZone ${description}] Position check:`, {
                cursorX: x,
                cursorY: y,
                rectLeft: rect.left,
                rectRight: rect.right,
                rectTop: rect.top,
                rectBottom: rect.bottom,
                dpr: window.devicePixelRatio
              });

              let isOver = (x >= rect.left && x <= rect.right && y >= rect.top && y <= rect.bottom);

              // If not over, try WITH DPR correction (for high-DPI screens)
              if (!isOver) {
                const dpr = window.devicePixelRatio || 1;
                x = event.payload.position.x / dpr;
                y = event.payload.position.y / dpr;
                isOver = (x >= rect.left && x <= rect.right && y >= rect.top && y <= rect.bottom);
                console.log(`[FileUploadZone ${description}] Retrying with DPR correction:`, {
                  cursorX: x,
                  cursorY: y,
                  isOver
                });
              }

              if (isOver && !isAtLimit) {
                console.log(`[FileUploadZone ${description}] ✅ Cursor is OVER this zone, setting as active`);
                setIsDragOver(true);
                setActiveZoneId(zoneId);
                activeZoneIdRef.current = zoneId;
                dragCounterRef.current = 1; // Reset counter
              } else if (activeZoneIdRef.current === zoneId && !isOver) {
                // Left this zone
                console.log(`[FileUploadZone ${description}] ❌ Cursor LEFT this zone`);
                setIsDragOver(false);
                setActiveZoneId(null);
                activeZoneIdRef.current = null;
                dragCounterRef.current = 0;
              }
            }
          } else if (event.payload.type === "drop") {
            const currentActiveZone = activeZoneIdRef.current;
            console.log(`[FileUploadZone ${description}] 🎯 DROP detected, activeZone:`, currentActiveZone, 'thisZone:', zoneId);

            // Only process if this is the active zone
            if (currentActiveZone === zoneId && event.payload.paths && event.payload.paths.length > 0) {
              try {
                console.log(`[FileUploadZone ${description}] 📁 Converting ${event.payload.paths.length} paths:`, event.payload.paths);
                const files = await pathsToFiles(event.payload.paths);
                console.log(`[FileUploadZone ${description}] ✅ Converted ${files.length} files successfully`);
                handleNewFiles(files);
              } catch (error) {
                console.error(`[FileUploadZone ${description}] ❌ Error converting files:`, error);
                setErrorMessage("Erreur lors de la lecture des fichiers.");
              }
            } else {
              console.log(`[FileUploadZone ${description}] ⏭️ Ignoring drop (not active zone or no paths)`);
            }

            // Reset state after drop
            setIsDragOver(false);
            setActiveZoneId(null);
            activeZoneIdRef.current = null;
            dragCounterRef.current = 0;
          } else if (event.payload.type === "leave") {
            console.log(`[FileUploadZone ${description}] 👋 Drag LEAVE event`);
            // Only clear if this was the active zone
            if (activeZoneIdRef.current === zoneId) {
              setIsDragOver(false);
              setActiveZoneId(null);
              activeZoneIdRef.current = null;
              dragCounterRef.current = 0;
            }
          } else if (event.payload.type === "cancel") {
            console.log(`[FileUploadZone ${description}] 🚫 Drag CANCELLED`);
            setIsDragOver(false);
            setActiveZoneId(null);
            activeZoneIdRef.current = null;
            dragCounterRef.current = 0;
          }
        });

        if (!unlisten || typeof unlisten !== 'function') {
          console.error(`[FileUploadZone ${description}] ❌ unlisten is not a function:`, typeof unlisten);
          return;
        }

        if (isMounted) {
          unlistenDrop = unlisten;
          isListenerRegistered = true;
          console.log(`[FileUploadZone ${description}] ✅ Tauri listeners setup complete`);
        } else {
          // Component unmounted during setup, cleanup immediately
          try {
            unlisten();
          } catch (error) {
            console.error(`[FileUploadZone ${description}] Error calling unlisten during setup:`, error);
          }
        }
      } catch (error) {
        console.error(`[FileUploadZone ${description}] ❌ Failed to setup Tauri listeners:`, error);
      }
    };

    setupListeners();

    return () => {
      isMounted = false;

      // Only try to cleanup if the listener was successfully registered
      if (isListenerRegistered && unlistenDrop) {
        // Skip cleanup in development mode to avoid hot reload issues
        // Listeners will be automatically cleaned up when window closes
        const isDev = process.env.NODE_ENV === 'development';

        if (isDev) {
          console.log(`[FileUploadZone ${description}] Skipping listener cleanup in dev mode`);
          return;
        }

        // In production, defer cleanup to avoid race conditions
        setTimeout(() => {
          try {
            // Extra safety checks before calling unlisten
            if (typeof unlistenDrop !== 'function') {
              return;
            }

            // Verify Tauri environment still exists
            const isTauriEnv = typeof window !== 'undefined' &&
                              ((window as any).__TAURI_INTERNALS__ || (window as any).__TAURI__);

            if (!isTauriEnv) {
              return;
            }

            console.log(`[FileUploadZone ${description}] 🧹 Cleaning up listeners`);
            unlistenDrop();
          } catch (error) {
            // Silently ignore cleanup errors
          }
        }, 0);
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [description, zoneId, isAtLimit]);

  return (
    <div className="space-y-4">
      {/* Zone de drop - masquée quand limite atteinte */}
      {!isAtLimit && (
        <div className="relative" style={{ isolation: 'isolate' }}>
          {/* Drag overlay with animations */}
          {isDragOver && (
            <>
              {/* Primary glow - moving gradient yellow/blue mix */}
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
              {/* Animated dashed border SVG */}
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
          )}

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
                // Only use HTML5 drag events in browser (dev mode)
                const isTauri = (window as any).__TAURI_INTERNALS__ || (window as any).__TAURI__;
                if (!isTauri) {
                  dragCounterRef.current++;
                  if (dragCounterRef.current === 1 && !isAtLimit) {
                    console.log(`[FileUploadZone ${description}] HTML5 DragEnter`);
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
                // Only use HTML5 drag events in browser (dev mode)
                const isTauri = (window as any).__TAURI_INTERNALS__ || (window as any).__TAURI__;
                if (!isTauri) {
                  dragCounterRef.current--;
                  if (dragCounterRef.current === 0) {
                    console.log(`[FileUploadZone ${description}] HTML5 DragLeave`);
                    setIsDragOver(false);
                    setActiveZoneId(null);
                  }
                }
              }}
              onDrop={(e) => {
                e.preventDefault();
                e.stopPropagation();

                // Only use HTML5 drag events in browser (dev mode)
                // In Tauri, files come via onDragDropEvent
                const isTauri = (window as any).__TAURI_INTERNALS__ || (window as any).__TAURI__;
                if (!isTauri) {
                  dragCounterRef.current = 0;
                  setIsDragOver(false);

                  if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
                    console.log(`[FileUploadZone ${description}] HTML5 Drop with ${e.dataTransfer.files.length} files`);
                    handleNewFiles(Array.from(e.dataTransfer.files));
                    setActiveZoneId(null);
                  }
                }
              }}
            >
              {/* Title */}
              <p className="mb-4 text-center font-medium text-foreground">
                {description}
              </p>

              {/* Icon and counter */}
              <div className="flex items-center space-x-4 mb-4">
                <div className="p-3 rounded-lg bg-secondary">
                  <Upload
                    className={`text-secondary-foreground ${
                      isDragOver ? "animate-bounce-smooth" : "group-hover-bounce-smooth"
                }`} size={24} />
              </div>

              <div className="text-sm">
                <div className="font-semibold text-foreground">
                  {selectedFiles.length} / {maxFiles} fichier(s)
                </div>
                <div className="text-muted-foreground text-xs">
                  {`${remainingSlots} restant(s)`}
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

              {/* Helper text */}
              <p className="text-sm text-muted-foreground">
                Glissez-déposez vos fichiers ou cliquez pour parcourir
              </p>
            </label>
          </div>
        </div>
      )}

      {/* Liste des fichiers */}
      {selectedFiles.length > 0 && (
        <div className="space-y-2 ">
          <div className="flex items-center gap-3">
            <h4 className="text-sm font-semibold text-foreground">
              {isAtLimit
                ? `${description} - Fichiers sélectionnés (${selectedFiles.length}/${maxFiles})`
                : `Fichiers sélectionnés (${selectedFiles.length})`
              }
            </h4>
            {isAtLimit && (
              <span className="text-xs border border-orange-500 text-orange-600 bg-orange-50 px-2 py-1 rounded-full">
                Limite atteinte
              </span>
            )}
          </div>
          <div className="space-y-2 max-h-60 overflow-y-auto">
            {selectedFiles.map((file, index) => {
              const IconComponent = getFileIcon(file);
              return (
                <div
                  key={`${file.name}-${index}`}
                  className="flex items-center justify-between p-3 bg-card border border-border rounded-lg hover:bg-muted/30 transition-colors"
                >
                  <div className="flex items-center space-x-3 flex-1 min-w-0">
                    <IconComponent 
                      className="text-muted-foreground flex-shrink-0" 
                      size={18} 
                    />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-foreground truncate">
                        {file.name}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {formatFileSize(file.size)}
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={() => removeFile(index)}
                    className="p-1 text-muted-foreground hover:text-destructive hover:bg-destructive/10 rounded transition-colors flex-shrink-0 ml-2"
                    aria-label={`Supprimer ${file.name}`}
                  >
                    <X size={16} className="cursor-pointer hover:text-red-600" />
                  </button>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Message d'erreur */}
      {!!errorMessage && (
        <div className="bg-destructive/10 border border-destructive/20 rounded-lg p-3">
          <div className="flex items-center">
            <span className="text-destructive">⚠️</span>
            <p className="text-sm text-destructive ml-3">{errorMessage}</p>
          </div>
        </div>
      )}
    </div>
  );
}
