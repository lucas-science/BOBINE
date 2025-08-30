"use client";
import React from "react";
import { FILE_ZONE } from "@/src/lib/utils/uploadFile.utils";
import FileUploadCard from "@/app/components/upload/FileUploadCard";
import { useUploadState } from "@/src/hooks/useUploadState";
import { copyAllFilesToDocuments } from "@/src/lib/copyAllFilesToDocuments";
import { getIndexByPathname, getNavigationByIndex } from "@/src/lib/pathNavigation";
import { usePathname, useRouter } from "next/navigation";
import {
  checkContext,
  getContextB64,
  getContextMasses,
  getDocumentsDir,
} from "@/src/lib/utils/invoke.utils";
import BackButton from "./components/backButton";
import NextButton from "./components/nextButton";

import LoaderOverlay from "@/app/components/LoaderOverlay";

export default function UploadPage() {
  const router = useRouter();
  const pathname = usePathname();

  const stepIndex = getIndexByPathname(pathname);
  const [prevPath, nextPath] = getNavigationByIndex(stepIndex);
  const { allFilesByZoneKey, handleFilesChange, setAllFilesByZoneKey } = useUploadState();

  // ----- Loader overlay state -----
  const [overlayOpen, setOverlayOpen] = React.useState(false);
  const TOTAL_STEPS = 4; // 1) copie 2) préparation 3) vérification 4) lecture contexte si besoin
  const [currentStep, setCurrentStep] = React.useState(0);
  const [currentTask, setCurrentTask] = React.useState("Préparation…");

  // ----- Error state -----
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

      const is_context_ok: boolean = await runStep<boolean>(3, "Vérification du contexte…", async () =>
        checkContext(docsDir)
      );

      if (is_context_ok) {
        await runStep(4, "Chargement du contexte…", async () => {
          const masses = await getContextMasses(docsDir);
          localStorage.setItem("app_context_masses", JSON.stringify(masses));
          const context_b64 = await getContextB64(docsDir);
          localStorage.setItem("app_context_b64", context_b64);
        });
      }

      // terminé
      setOverlayOpen(false);
      setAllFilesByZoneKey({});
      router.push(nextPath);
    } catch (e) {
      // en cas d'erreur, on ferme proprement et affiche l'erreur
      setOverlayOpen(false);
      console.error(e);
      
      // Formatage de l'erreur pour l'affichage
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

  return (
    <div className="min-h-screen">
      <div className="max-w-6xl mx-auto pb-24">
        <h1 className="text-2xl font-bold text-gray-900 mb-6">File Upload Center</h1>

        {/* Error display */}
        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex items-start">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.28 7.22a.75.75 0 00-1.06 1.06L8.94 10l-1.72 1.72a.75.75 0 101.06 1.06L10 11.06l1.72 1.72a.75.75 0 101.06-1.06L11.06 10l1.72-1.72a.75.75 0 00-1.06-1.06L10 8.94 8.28 7.22z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3 flex-1">
                <h3 className="text-sm font-medium text-red-800">
                  Erreur lors du traitement
                </h3>
                <div className="mt-1 text-sm text-red-700">
                  {error}
                </div>
                <div className="mt-3">
                  <button
                    type="button"
                    className="bg-red-50 text-red-800 rounded-md px-3 py-1.5 text-sm font-medium hover:bg-red-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
                    onClick={dismissError}
                  >
                    Fermer
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

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