"use client";
import React from "react";
import FileUploadZone from "./FileUploadZone";
import { FILE_ZONE } from "@/src/lib/utils/uploadFile.utils";
import { UPLOAD_SUBZONE_DISPLAY_NAMES } from "@/src/lib/config/constants";

export interface FileUploadCardProps {
  title: string;
  zoneKey: keyof typeof FILE_ZONE;
  onFilesChange: (zoneKey: string, filesByZone: File[][]) => void;
}

export default function FileUploadCard({ title, zoneKey, onFilesChange }: FileUploadCardProps) {
  const zonesConfig = FILE_ZONE[zoneKey];
  const [filesByZone, setFilesByZone] = React.useState<File[][]>(
    () => Array.from({ length: zonesConfig.length }, () => [])
  );

  React.useEffect(() => { onFilesChange(zoneKey, filesByZone); }, [filesByZone, zoneKey, onFilesChange]);

  const getSubZoneLabel = (zoneName: string) => {
    return UPLOAD_SUBZONE_DISPLAY_NAMES[zoneName as keyof typeof UPLOAD_SUBZONE_DISPLAY_NAMES]
      || `${zoneName.charAt(0).toUpperCase() + zoneName.slice(1)} files`;
  };

  return (
    <div className="bg-white p-4 h-fit rounded-lg shadow-md border border-gray-200">
      <div className="mb-4 flex justify-between items-center">
        <h2 className="text-lg font-semibold text-gray-800">{title}</h2>
      </div>

      <div className="space-y-6">
        {zonesConfig.map((zoneItem, index) => (
          <FileUploadZone
            key={index}
            description={getSubZoneLabel(zoneItem.zone)}
            selectedFiles={filesByZone[index] || []}
            maxFiles={zoneItem.max_files}
            onFileSelect={(files: File[]) =>
              setFilesByZone((prev) => {
                const next = [...prev];
                next[index] = files;
                return next;
              })
            }
          />
        ))}
      </div>
    </div>
  );
}
