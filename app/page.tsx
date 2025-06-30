"use client";
import React, { useCallback, useState, useEffect } from "react";
import { FILE_ZONE } from "@/src/lib/utils/uploadFile.utils";
import { Upload } from "lucide-react";
import { invoke } from "@tauri-apps/api/core";

interface FileUploadZoneProps {
  description: string;
  onFileSelect: (files: File[]) => void;
  selectedFiles: File[];
  maxFiles: number;
  zoneIndex: number;
}

const FileUploadZone: React.FC<FileUploadZoneProps> = ({
  description,
  onFileSelect,
  selectedFiles,
  maxFiles,
}) => {
  const [isDragOver, setIsDragOver] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string>("");

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const newFiles = Array.from(event.target.files || []);
    handleNewFiles(newFiles);
  };

  const handleNewFiles = (newFiles: File[]) => {
    setErrorMessage("");

    if (selectedFiles.length + newFiles.length > maxFiles) {
      setErrorMessage(`Limite dépassée ! Maximum ${maxFiles} fichier(s) par zone.`);
      return;
    }

    const updatedFiles = [...selectedFiles, ...newFiles];
    onFileSelect(updatedFiles);
  };

  const handleDragOver = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragOver(false);
    const newFiles = Array.from(event.dataTransfer.files || []);
    handleNewFiles(newFiles);
  };

  const isAtLimit = selectedFiles.length >= maxFiles;
  const remainingSlots = maxFiles - selectedFiles.length;

  return (
    <div className="space-y-3">
      <div
        className={`
          border-2 border-dashed p-4 rounded-lg flex flex-col items-center justify-center transition-all duration-200
          ${isDragOver ? "border-blue-400 bg-blue-50" : "border-gray-300"}
          ${isAtLimit ? "bg-gray-50 opacity-60" : "bg-gray-50 hover:bg-gray-100"}
        `}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <label className={`cursor-pointer flex flex-col justify-center items-center w-full ${isAtLimit ? "cursor-not-allowed" : ""}`}>
          <p className="text-gray-600 mb-4 text-center">{description}</p>

          <div className="flex items-center space-x-4 mb-3">
            <div className={`p-2 rounded-lg transition-colors ${isAtLimit ? "bg-gray-400" : "bg-blue-500 hover:bg-blue-600"}`}>
              <Upload className="text-white" size={20} />
            </div>

            <div className="text-sm">
              <div className={`font-medium ${isAtLimit ? "text-red-600" : "text-gray-700"}`}>
                {selectedFiles.length} / {maxFiles} fichier(s)
              </div>
              <div className="text-gray-500 text-xs">
                {isAtLimit ? "Limite atteinte" : `${remainingSlots} restant(s)`}
              </div>
            </div>
          </div>

          <input
            type="file"
            multiple={maxFiles > 1}
            onChange={handleFileChange}
            className="hidden"
            disabled={isAtLimit}
          />

          <p className={`text-sm ${isAtLimit ? "text-gray-400" : "text-gray-500"}`}>
            {isAtLimit ? "Limite atteinte" : "Drag and drop or click to upload"}
          </p>
        </label>
      </div>

      {errorMessage && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-3">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <span className="text-red-400">⚠️</span>
            </div>
            <div className="ml-3">
              <p className="text-sm text-red-700">{errorMessage}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

interface FileUploadCardProps {
  title: string;
  zoneKey: keyof typeof FILE_ZONE;
  onFilesChange: (zoneKey: string, filesByZone: File[][]) => void;
}

const FileUploadCard: React.FC<FileUploadCardProps> = ({ title, zoneKey, onFilesChange }) => {
  const zonesConfig = FILE_ZONE[zoneKey];
  const [filesByZone, setFilesByZone] = useState<File[][]>(
    () => Array.from({ length: zonesConfig.length }, () => [])
  );

  // Utiliser useEffect pour notifier le parent après le rendu
  useEffect(() => {
    onFilesChange(zoneKey, filesByZone);
  }, [filesByZone, zoneKey, onFilesChange]);

  const handleFileSelect = (files: File[], zoneIndex: number) => {
    setFilesByZone((prev) => {
      const updated = [...prev];
      updated[zoneIndex] = files;
      return updated;
    });
  };

  return (
    <div className="bg-white p-4 h-fit rounded-lg shadow-md border border-gray-200">
      <div className="mb-4">
        <div className="flex justify-between items-center">
          <h2 className="text-lg font-semibold text-gray-800">{title}</h2>
        </div>
      </div>

      <div className="space-y-6">
        {zonesConfig.map((zoneItem, index) => (
          <FileUploadZone
            key={index}
            description={`${zoneItem.zone.charAt(0).toUpperCase() + zoneItem.zone.slice(1)} files`}
            onFileSelect={(files) => handleFileSelect(files, index)}
            selectedFiles={filesByZone[index] || []}
            maxFiles={zoneItem.max_files}
            zoneIndex={index}
          />
        ))}
      </div>
    </div>
  );
};

const UploadPage = () => {
  const [allFilesByZoneKey, setAllFilesByZoneKey] = useState<Record<string, File[][]>>({});

  // Stabiliser la fonction avec useCallback pour éviter les re-renders inutiles
  const handleFilesChange = useCallback((key: string, filesByZone: File[][]) => {
    setAllFilesByZoneKey((prev) => {
      // Vérifier si les données ont vraiment changé pour éviter les mises à jour inutiles
      const currentData = prev[key];
      if (JSON.stringify(currentData) !== JSON.stringify(filesByZone)) {
        return { ...prev, [key]: filesByZone };
      }
      return prev;
    });
  }, []);

  const handleCopyFiles = async () => {
  try {
    const docsDir: string = await invoke("get_documents_dir");

    // Supprimer les dossiers existants
    for (const zoneKey of Object.keys(FILE_ZONE)) {
      const zonePath = `${docsDir}/${zoneKey}`;
      console.log(`🗑️ Suppression du dossier ${zonePath}...`);
      await invoke("remove_dir", { dirPath: zonePath });
    }

    // Copier les fichiers dans les nouveaux dossiers
    for (const [zoneKey, zoneFilesArray] of Object.entries(allFilesByZoneKey)) {
      const zoneDefs = FILE_ZONE[zoneKey as keyof typeof FILE_ZONE];

      for (let zoneIndex = 0; zoneIndex < zoneDefs.length; zoneIndex++) {
        const files = zoneFilesArray[zoneIndex] || [];
        const zoneName = zoneDefs[zoneIndex].zone;
        const zonePath = `${docsDir}/${zoneKey}/${zoneName}`;

        for (const file of files) {
          const destName = `${file.name}`;
          const destPath = `${zonePath}/${destName}`;

          console.log(`📋 Copie de ${file.name} → ${destPath}...`);

          const buffer = await file.arrayBuffer();
          const arr = Array.from(new Uint8Array(buffer));

          await invoke("write_file", {
            destinationPath: destPath,
            contents: arr,
          });

          console.log(`✅ ${file.name} copié sous ${destName}`);
        }
      }
    }

    console.log("🎉 Copie terminée !");
    setAllFilesByZoneKey({});
  } catch (err) {
    console.error("❌ Erreur de copie :", err);
  }
};

  return (
    <div className="min-h-screen">
      <div className="max-w-6xl mx-auto">
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

        <button
          className="mt-8 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
          onClick={handleCopyFiles}
        >
          📁 Copier tous les fichiers
        </button>
      </div>
    </div>
  );
};

export default UploadPage;