import React from "react";
import { X } from "lucide-react";
import { getFileIcon, formatFileSize } from "@/src/lib/utils/fileHelpers";

interface FileListItemProps {
  file: File;
  onRemove: () => void;
}

/**
 * Single file item in the upload list
 */
export default function FileListItem({ file, onRemove }: FileListItemProps) {
  const IconComponent = getFileIcon(file);

  return (
    <div className="flex items-center justify-between p-3 bg-card border border-border rounded-lg hover:bg-muted/30 transition-colors">
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
        onClick={onRemove}
        className="p-1 text-muted-foreground hover:text-destructive hover:bg-destructive/10 rounded transition-colors flex-shrink-0 ml-2"
        aria-label={`Supprimer ${file.name}`}
      >
        <X size={16} className="cursor-pointer hover:text-red-600" />
      </button>
    </div>
  );
}
