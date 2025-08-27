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

// ⬇️ ajoute ce composant (créé précédemment)
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

  const runStep = async (n: number, label: string, fn: () => Promise<any>) => {
    setCurrentStep(n);
    setCurrentTask(label);
    return await fn();
  };

  const handleNext = async () => {
    if (!nextPath) return;

    setOverlayOpen(true);
    setCurrentStep(0);
    setCurrentTask("Préparation…");

    try {
      // 1) Copie des fichiers
      const ok = await runStep(1, "Copie des fichiers…", async () =>
        copyAllFilesToDocuments(allFilesByZoneKey)
      );

      if (!ok) {
        // copie échouée → on ferme l’overlay et on sort
        setOverlayOpen(false);
        return;
      }

      // 2) Préparation du dossier Documents de l’app
      const docsDir: string = await runStep(2, "Préparation du dossier…", async () =>
        getDocumentsDir()
      );

      // 3) Vérification du contexte
      const is_context_ok: boolean = await runStep(3, "Vérification du contexte…", async () =>
        checkContext(docsDir)
      );

      // 4) Si nécessaire : lecture/stockage du contexte
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
      // en cas d’erreur, on ferme proprement
      setOverlayOpen(false);
      console.error(e);
    }
  };

  const handleBack = () => {
    if (prevPath) router.push(prevPath);
  };

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
