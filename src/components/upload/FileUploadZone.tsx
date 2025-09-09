"use client";
import React, { useState } from "react";
import { Upload, X, File, FileText, FileImage, FileVideo } from "lucide-react";

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

  const removeFile = (indexToRemove: number) => {
    const updatedFiles = selectedFiles.filter((_, index) => index !== indexToRemove);
    onFileSelect(updatedFiles);
    setErrorMessage("");
  };

  return (
    <div className="space-y-4">
      {/* Zone de drop - masquée quand limite atteinte */}
      {!isAtLimit && (
        <div
          className={`
            border-2 border-dashed p-6 rounded-lg flex flex-col items-center justify-center 
            transition-all duration-200
            ${isDragOver 
              ? "border-primary bg-primary/5" 
              : "border-border"
            }
            bg-background hover:bg-muted/30 cursor-pointer
          `}
          onDragOver={(e) => { e.preventDefault(); setIsDragOver(true); }}
          onDragLeave={(e) => { e.preventDefault(); setIsDragOver(false); }}
          onDrop={(e) => {
            e.preventDefault(); setIsDragOver(false);
            handleNewFiles(Array.from(e.dataTransfer.files || []));
          }}
        >
          <label className="cursor-pointer flex flex-col justify-center items-center w-full">
            <p className="text-foreground mb-4 text-center font-medium">{description}</p>

            <div className="flex items-center space-x-4 mb-4">
              <div className="p-3 rounded-lg transition-colors bg-secondary hover:bg-secondary/80">
                <Upload className="text-secondary-foreground" size={24} />
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

            <p className="text-sm text-muted-foreground">
              Glissez-déposez vos fichiers ou cliquez pour parcourir
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
            <span className="text-xs border px-2 py-1 rounded-full">
              Limite atteinte
            </span>
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
