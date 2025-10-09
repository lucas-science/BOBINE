import React from "react";
import FileListItem from "./FileListItem";

interface FileListProps {
  files: File[];
  description: string;
  maxFiles: number;
  onRemoveFile: (index: number) => void;
}

/**
 * List of uploaded files with remove buttons
 */
export default function FileList({
  files,
  description,
  maxFiles,
  onRemoveFile,
}: FileListProps) {
  if (files.length === 0) return null;

  const isAtLimit = files.length >= maxFiles;

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-3">
        <h4 className="text-sm font-semibold text-foreground">
          {isAtLimit
            ? `${description} - Fichiers sélectionnés (${files.length}/${maxFiles})`
            : `Fichiers sélectionnés (${files.length})`
          }
        </h4>
        {isAtLimit && (
          <span className="text-xs border border-orange-500 text-orange-600 bg-orange-50 px-2 py-1 rounded-full">
            Limite atteinte
          </span>
        )}
      </div>
      <div className="space-y-2 max-h-60 overflow-y-auto">
        {files.map((file, index) => (
          <FileListItem
            key={`${file.name}-${index}`}
            file={file}
            onRemove={() => onRemoveFile(index)}
          />
        ))}
      </div>
    </div>
  );
}
