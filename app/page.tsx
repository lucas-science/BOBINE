"use client";
import React from "react";
import { FILE_ZONE } from "@/src/lib/utils/uploadFile.utils";
import FileUploadCard from "@/src/components/upload/FileUploadCard";
import { useUploadState } from "@/src/hooks/useUploadState";
import { copyAllFilesToDocuments } from "@/src/lib/copyAllFilesToDocuments";
import { getIndexByPathname, getNavigationByIndex } from "@/src/lib/pathNavigation";
import { usePathname, useRouter } from "next/navigation";
import { tauriService } from "@/src/lib/services/TauriService";
import BackButton from "@/src/components/shared/backButton";
import NextButton from "@/src/components/shared/nextButton";
import LoaderOverlay from "@/src/components/upload/LoaderOverlay";
import ErrorAlert from "@/src/components/upload/ErrorAlert";
import { info } from "@tauri-apps/plugin-log";

export default function Page() {
  const router = useRouter();
  const pathname = usePathname();

  const stepIndex = getIndexByPathname(pathname);
  const [prevPath, nextPath] = getNavigationByIndex(stepIndex);
  const { allFilesByZoneKey, handleFilesChange, setAllFilesByZoneKey } = useUploadState();

  const [overlayOpen, setOverlayOpen] = React.useState(false);
  const TOTAL_STEPS = 3;
  const [currentStep, setCurrentStep] = React.useState(0);
  const [currentTask, setCurrentTask] = React.useState("Préparation…");

  const [error, setError] = React.useState<string | null>(null);

  async function runStep<T>(n: number, label: string, fn: () => Promise<T>): Promise<T> {
    setCurrentStep(n);
    setCurrentTask(label);
    return await fn();
  }

  const handleNext = async () => {
    if (!nextPath) return;

    // Reset error state
    setError(null);
    setOverlayOpen(true);
    setCurrentStep(0);
    setCurrentTask("Préparation…");

    try {
      const ok = await runStep<boolean>(1, "Copie des fichiers…", async () =>
        copyAllFilesToDocuments(allFilesByZoneKey)
      );

      if (!ok) {
        setOverlayOpen(false);
        setError("Échec de la copie des fichiers. Vérifiez vos fichiers et réessayez.");
        return;
      }

      const docsDir: string = await runStep<string>(2, "Préparation du dossier…", async () =>
        tauriService.getDocumentsDir()
      );

      if (!docsDir) {
        setOverlayOpen(false);
        setError("Impossible d'accéder au dossier des documents.");
        return;
      }

      const contextValidation = await runStep(3, "Vérification du contexte…", async () =>
        tauriService.validateContext(docsDir)
      );
      info("Context validation result: " + JSON.stringify(contextValidation));
      if (!contextValidation.valid) {
        setOverlayOpen(false);
        setError(contextValidation.error_message);
        return;
      }

      // terminé
      setOverlayOpen(false);
      setAllFilesByZoneKey({});
      router.push(nextPath);
    } catch (e) {
      setOverlayOpen(false);
      console.error(e);

      let errorMessage = "Une erreur inattendue s'est produite.";

      if (e instanceof Error) {
        errorMessage = e.message;
      } else if (typeof e === "string") {
        errorMessage = e;
      } else if (e && typeof e === "object" && "message" in e) {
        errorMessage = String(e.message);
      }

      setError(errorMessage);
    }
  };

  const handleBack = () => {
    if (prevPath) router.push(prevPath);
  };

  const dismissError = () => {
    setError(null);
  };

  const getZoneDisplayName = (zoneKey: string) => {
    const zoneNames: Record<string, string> = {
      context: "Context",
      pignat: "Pignat", 
      chromeleon: "Chromeleon",
      chromeleon_online_permanent_gas: "Chromeleon online Permanent Gas"
    };
    return zoneNames[zoneKey] || zoneKey.charAt(0).toUpperCase() + zoneKey.slice(1);
  };

  return (
    <div className="min-h-screen">
      {/* ErrorAlert sticky en haut avec z-index approprié */}
      <div className="sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-4">
          <ErrorAlert
            error={error}
            onDismiss={dismissError}
            title="Erreur lors du traitement"
          />
        </div>
      </div>

      {/* Contenu principal */}
      <div className="max-w-6xl mx-auto pb-24">
        <h1 className="text-2xl font-bold text-gray-900 mb-6">File Upload Center</h1>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {Object.keys(FILE_ZONE).map((zoneKey) => (
            <FileUploadCard
              key={zoneKey}
              title={getZoneDisplayName(zoneKey)}
              zoneKey={zoneKey as keyof typeof FILE_ZONE}
              onFilesChange={handleFilesChange}
            />
          ))}
        </div>
      </div>

      <div className="fixed bottom-0 left-0 right-0 p-4 z-50">
        <div className="flex justify-between items-center w-full mx-auto">
          <BackButton onClick={handleBack} disable={!prevPath} />
          <NextButton onClick={handleNext} disable={!nextPath} />
        </div>
      </div>

      {/* ----- Overlay au premier plan ----- */}
      <LoaderOverlay
        open={overlayOpen}
        currentStep={Math.min(currentStep, TOTAL_STEPS)}
        totalSteps={TOTAL_STEPS}
        currentTask={currentTask}
      />
    </div>
  );
}