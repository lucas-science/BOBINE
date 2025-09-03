"use client";
import React from "react";
import { FILE_ZONE } from "@/src/lib/utils/uploadFile.utils";
import FileUploadCard from "@/app/components/upload/FileUploadCard";
import { useUploadState } from "@/src/hooks/useUploadState";
import { copyAllFilesToDocuments } from "@/src/lib/copyAllFilesToDocuments";
import { getIndexByPathname, getNavigationByIndex } from "@/src/lib/pathNavigation";
import { usePathname, useRouter } from "next/navigation";
import { checkContext, getDocumentsDir } from "@/src/lib/utils/invoke.utils";
import BackButton from "./components/backButton";
import NextButton from "./components/nextButton";
import LoaderOverlay from "@/app/components/LoaderOverlay";
import ErrorAlert from "@/app/components/ErrorAlert";

export default function UploadPage() {
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
        getDocumentsDir()
      );

      if (!docsDir) {
        setOverlayOpen(false);
        setError("Impossible d'accéder au dossier des documents.");
        return;
      }

      const is_context_ok: boolean = await runStep<boolean>(3, "Vérification du contexte…", async () =>
        checkContext(docsDir)
      );

      if (!is_context_ok) {
        setOverlayOpen(false);
        setError("Le contexte des fichiers est invalide. Vérifiez vos fichiers et réessayez.");
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
      pigna: "Pigna", 
      chromeleon: "Chromeleon",
      chromeleon_online_permanent_gas: "Chromeleon online Permanent Gas"
    };
    return zoneNames[zoneKey] || zoneKey.charAt(0).toUpperCase() + zoneKey.slice(1);
  };

  return (
    <div className="min-h-screen">
      <div className="max-w-6xl mx-auto pb-24">
        <h1 className="text-2xl font-bold text-gray-900 mb-6">File Upload Center</h1>

        {/* Error display using the ErrorAlert component */}
        <ErrorAlert
          error={error}
          onDismiss={dismissError}
          title="Erreur lors du traitement"
        />
        
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