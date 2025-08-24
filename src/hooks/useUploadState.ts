"use client";
import { useCallback, useMemo, useState } from "react";

export type FilesByZoneKey = Record<string, File[][]>;

export function useUploadState() {
  const [allFilesByZoneKey, setAllFilesByZoneKey] = useState<FilesByZoneKey>({});

  const handleFilesChange = useCallback((key: string, filesByZone: File[][]) => {
    setAllFilesByZoneKey((prev) => {
      const current = prev[key];
      if (JSON.stringify(current) !== JSON.stringify(filesByZone)) {
        return { ...prev, [key]: filesByZone };
      }
      return prev;
    });
  }, []);

  const hasAnyFile = useMemo(() => {
    const zoneKeys = Object.keys(allFilesByZoneKey);
    if (!zoneKeys.length) return false;
    return zoneKeys.some((z) => (allFilesByZoneKey[z] || []).some((arr) => (arr?.length || 0) > 0));
  }, [allFilesByZoneKey]);

  return { allFilesByZoneKey, handleFilesChange, hasAnyFile, setAllFilesByZoneKey };
}
