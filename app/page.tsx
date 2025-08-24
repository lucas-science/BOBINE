"use client";
import React from "react";
import { FILE_ZONE } from "@/src/lib/utils/uploadFile.utils";
import FileUploadCard from "@/app/components/upload/FileUploadCard";
import { useUploadState } from "@/src/hooks/useUploadState";
import { copyAllFilesToDocuments } from "@/src/lib/copyAllFilesToDocuments";
import { getIndexByPathname, getNavigationByIndex } from "@/src/lib/pathNavigation";
import { usePathname, useRouter } from "next/navigation";

export default function UploadPage() {
  const router = useRouter();
  const pathname = usePathname();

  const step = getIndexByPathname(pathname);
  const [prevPath, nextPath] = getNavigationByIndex(step);

  const { allFilesByZoneKey, handleFilesChange, hasAnyFile, setAllFilesByZoneKey } = useUploadState();
  const [isCopying, setIsCopying] = React.useState(false);

  const handleNext = async () => {
    if (!nextPath) return;
    setIsCopying(true);
    const ok = await copyAllFilesToDocuments(allFilesByZoneKey);
    setIsCopying(false);
    if (ok) {
      setAllFilesByZoneKey({});
      router.push(nextPath);
    }
  };

  const handleBack = () => { if (prevPath) router.push(prevPath); };

  return (
    <div className="min-h-screen">
      <div className="max-w-6xl mx-auto pb-24">
        <h1 className="text-2xl font-bold text-gray-900 mb-6">File Upload Center</h1>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {Object.keys(FILE_ZONE).map((zoneKey) => (
            <FileUploadCard
              key={zoneKey}
              title={zoneKey.charAt(0).toUpperCase() + zoneKey.slice(1)}
              zoneKey={zoneKey as keyof typeof FILE_ZONE}
              onFilesChange={handleFilesChange}
            />
          ))}
        </div>
      </div>

      <div className="fixed bottom-0 left-0 right-0 bg-amber-300 p-4 z-50">
        <div className="flex justify-between items-center w-full mx-auto">
          <button
            onClick={handleBack}
            disabled={!prevPath}
            className={`px-4 py-2 rounded-lg border border-gray-800 text-gray-900 bg-white shadow-sm transition
              ${!prevPath ? "opacity-50 cursor-not-allowed" : "hover:bg-gray-50"}`}>
            ◀️ Retour
          </button>

          <button
            onClick={handleNext}
            disabled={!nextPath || !hasAnyFile || isCopying}
            className={`px-4 py-2 rounded-lg text-white bg-blue-600 shadow-sm transition
              ${(!nextPath || !hasAnyFile || isCopying) ? "opacity-50 cursor-not-allowed" : "hover:bg-blue-700"}`}>
            {isCopying ? "Copie en cours…" : "Suivant ▶️"}
          </button>
        </div>
      </div>
    </div>
  );
}
