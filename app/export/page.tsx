"use client";

import { usePathname, useRouter } from "next/navigation";
import { save } from "@tauri-apps/plugin-dialog";
import BackButton from "@/src/components/shared/backButton";
import { getIndexByPathname, getNavigationByIndex } from "@/src/lib/pathNavigation";
import { useState } from "react";
import { useNavigationWithLoader } from "@/src/hooks/useNavigationWithLoader";
import { StepLoader } from "@/src/components/shared/loaders";
import { tauriService } from "@/src/lib/services/TauriService";
import { toast } from "sonner";
import { Button } from "@/src/ui/button";
import { Card, CardDescription, CardHeader, CardTitle } from "@/src/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogTitle,
} from "@/src/components/ui/dialog";
import RestartButton from "@/src/components/export/restartButton";
import ButtonLoading from "@/src/components/export/buttonLoading";
import { info } from "@tauri-apps/plugin-log";

export default function Page() {
  const router = useRouter();
  const pathname = usePathname();
  const step = getIndexByPathname(pathname);
  const [prevPath] = getNavigationByIndex(step);

  const [loading, setLoading] = useState(false);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [savedPath, setSavedPath] = useState("");

  const { overlayOpen, handleNavigateWithLoader } = useNavigationWithLoader(prevPath || undefined);

  const handleGenerateExcel = async () => {
    setLoading(true);
    await new Promise<void>((r) => requestAnimationFrame(() => r()));

    try {
      const sel = localStorage.getItem("selectedMetrics");
      info("Selected metrics from localStorage:" + JSON.stringify(sel));
      if (!sel) throw new Error("Aucune métrique sélectionnée");
      const metrics = JSON.parse(sel);

      const docsDir = await tauriService.getDocumentsDir();

      // Générer un nom de fichier basé sur l'expérience
      let defaultName = "rapport.xlsx";
      try {
        const experienceName = await tauriService.getContextExperienceName(docsDir);
        defaultName = `${experienceName}.xlsx`;
      } catch (error) {
        console.warn("Failed to get experience name, using default:", error);
      }

      const absPath = await save({
        defaultPath: defaultName,
        filters: [{ name: "Excel", extensions: ["xlsx"] }],
      });
      if (!absPath) throw new Error("Enregistrement annulé");

      const res = await tauriService.generateAndSaveExcel(docsDir, metrics, absPath);
      if (!res || res.error) throw new Error(res?.error || "L'export a échoué");

      setSavedPath(res.result ?? absPath);
      setDialogOpen(true);
    } catch (e: unknown) {
      console.error(e);
      toast.error(
        e instanceof Error ? e.message : "Une erreur est survenue lors de l'export"
      );
    } finally {
      setLoading(false);
    }
  };

  const handleBack = async () => {
    if (!prevPath) return;
    await handleNavigateWithLoader(() => router.push(prevPath));
  };

  return (
    <>
      <div className="flex flex-col items-center justify-center w-full h-full">
        <Card className="mx-auto p-6 space-y-6 relative w-1/2 max-w-xl">
          <CardHeader>
            <CardTitle>Export de métriques</CardTitle>
            <CardDescription>
              Cliquez sur le bouton ci-dessous pour générer votre fichier Excel.
            </CardDescription>
          </CardHeader>

          {loading ? (
            <ButtonLoading />
          ) : (
            <Button
              onClick={handleGenerateExcel}
              className="w-full bg-secondary hover:bg-secondary/80 text-white cursor-pointer hover:rounded-lg transition-all"
            >
              Générer l&apos;Excel
            </Button>
          )}
        </Card>

        <div className="fixed bottom-4 left-0 right-0 px-6">
          <div className="flex justify-between">
            <BackButton onClick={handleBack} disable={!prevPath || loading} />
            <RestartButton onClick={() => router.push("/")} disable={loading} />
          </div>
        </div>
      </div>

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-w-md">
          <div className="text-center space-y-4 p-4">
            <DialogTitle className="text-xl font-semibold">
              Téléchargement terminé
            </DialogTitle>
            
            <DialogDescription className="text-muted-foreground">
              Votre fichier Excel a été enregistré avec succès.
            </DialogDescription>
            
            <div className="p-3 bg-muted rounded border text-left">
              <p className="text-sm text-muted-foreground mb-1">Emplacement :</p>
              <p className="font-mono text-sm break-all">{savedPath}</p>
            </div>
            
            <div className="flex gap-2 pt-2">
              <Button 
                onClick={() => setDialogOpen(false)}
                className="flex-1 cursor-pointer hover:rounded-lg transition-all"
              >
                OK
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      <StepLoader
        open={overlayOpen}
        currentStep={1}
        totalSteps={1}
        currentTask="Retour en cours…"
      />
    </>
  );
}
