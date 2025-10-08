"use client";
import React, { useState, useEffect, useId, useRef } from "react";
import { Upload, X, File, FileText, FileImage, FileVideo } from "lucide-react";
import { useFileDrop } from "@/src/contexts/FileDropContext";
import { getCurrentWindow } from "@tauri-apps/api/window";
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

  const isAtLimit = selectedFiles.length >= maxFiles;
  const remainingSlots = maxFiles - selectedFiles.length;
  const isThisZoneActive = activeZoneId === zoneId;

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

    const setupListeners = async () => {
      try {
        const appWindow = getCurrentWindow();

        // Listen for file drop events
        unlistenDrop = await appWindow.onFileDropEvent(async (event) => {
          console.log(`[FileUploadZone ${description}] File drop event:`, event);

          if (event.payload.type === "hover") {
            console.log(`[FileUploadZone ${description}] Hover detected`);
            // Don't set drag over here, let HTML events handle it
          } else if (event.payload.type === "drop") {
            console.log(`[FileUploadZone ${description}] Drop detected, active zone:`, activeZoneId);

            // Only process if this is the active zone
            if (isThisZoneActive && event.payload.paths && event.payload.paths.length > 0) {
              try {
                console.log(`[FileUploadZone ${description}] Converting paths:`, event.payload.paths);
                const files = await pathsToFiles(event.payload.paths);
                console.log(`[FileUploadZone ${description}] Converted ${files.length} files`);
                handleNewFiles(files);
              } catch (error) {
                console.error(`[FileUploadZone ${description}] Error converting files:`, error);
                setErrorMessage("Erreur lors de la lecture des fichiers.");
              }
            }

            setIsDragOver(false);
            dragCounterRef.current = 0;
            setActiveZoneId(null);
          } else if (event.payload.type === "cancel") {
            console.log(`[FileUploadZone ${description}] Drop cancelled`);
            setIsDragOver(false);
            dragCounterRef.current = 0;
            setActiveZoneId(null);
          }
        });

        console.log(`[FileUploadZone ${description}] Tauri listeners setup complete`);
      } catch (error) {
        console.log(`[FileUploadZone ${description}] Tauri API not available:`, error);
      }
    };

    setupListeners();

    return () => {
      if (unlistenDrop) unlistenDrop();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [description, isThisZoneActive]);

  return (
    <div className="space-y-4">
      {/* Zone de drop - masquée quand limite atteinte */}
      {!isAtLimit && (
        <div
          ref={dropZoneRef}
          className={`
            border-2 border-dashed p-6 rounded-lg flex flex-col items-center justify-center
            transition-all duration-300 ease-in-out
            ${isDragOver
              ? "border-primary border-4 bg-primary/15 scale-[1.03] shadow-xl ring-4 ring-primary/20"
              : "border-border bg-background hover:border-primary/30"
            }
            hover:bg-muted/30 cursor-pointer
          `}
          onDragEnter={(e) => {
            e.preventDefault();
            e.stopPropagation();
            dragCounterRef.current++;
            console.log(`[FileUploadZone ${description}] Drag enter, counter: ${dragCounterRef.current}`);
            if (dragCounterRef.current === 1 && !isAtLimit) {
              setIsDragOver(true);
              setActiveZoneId(zoneId);
              console.log(`[FileUploadZone ${description}] Set as active zone`);
            }
          }}
          onDragOver={(e) => {
            e.preventDefault();
            e.stopPropagation();
          }}
          onDragLeave={(e) => {
            e.preventDefault();
            e.stopPropagation();
            dragCounterRef.current--;
            console.log(`[FileUploadZone ${description}] Drag leave, counter: ${dragCounterRef.current}`);
            if (dragCounterRef.current === 0) {
              setIsDragOver(false);
              setActiveZoneId(null);
              console.log(`[FileUploadZone ${description}] Unset active zone`);
            }
          }}
          onDrop={(e) => {
            e.preventDefault();
            e.stopPropagation();
            console.log(`[FileUploadZone ${description}] HTML drop event received`);
            dragCounterRef.current = 0;
            setIsDragOver(false);

            // For HTML5 file selection (dev mode in browser only)
            // In Tauri, this will be empty and files come via onFileDropEvent
            if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
              console.log(`[FileUploadZone ${description}] Processing ${e.dataTransfer.files.length} files from HTML5 drop`);
              handleNewFiles(Array.from(e.dataTransfer.files));
              setActiveZoneId(null);
            }
          }}
        >
          <label className="cursor-pointer flex flex-col justify-center items-center w-full">
            <p className={`mb-4 text-center font-medium transition-all duration-300 ${
              isDragOver ? "text-primary text-lg" : "text-foreground"
            }`}>
              {isDragOver ? "Déposez les fichiers ici !" : description}
            </p>

            <div className="flex items-center space-x-4 mb-4">
              <div className={`p-3 rounded-lg transition-all duration-300 ${
                isDragOver
                  ? "bg-primary text-primary-foreground scale-110"
                  : "bg-secondary hover:bg-secondary/80"
              }`}>
                <Upload className={`transition-all duration-300 ${
                  isDragOver ? "text-primary-foreground animate-bounce" : "text-secondary-foreground"
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

            <p className={`text-sm transition-all duration-300 ${
              isDragOver ? "text-primary font-semibold" : "text-muted-foreground"
            }`}>
              {isDragOver ? "Relâchez pour ajouter" : "Glissez-déposez vos fichiers ou cliquez pour parcourir"}
            </p>
          </label>
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
