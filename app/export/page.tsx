"use client";

import { usePathname, useRouter } from "next/navigation";
import { save } from "@tauri-apps/plugin-dialog";
import { BaseDirectory, writeFile } from "@tauri-apps/plugin-fs";
import BackButton from "../components/backButton";
import { getIndexByPathname, getNavigationByIndex } from "@/src/lib/pathNavigation";
import { useState } from "react";
import { generateExcelFile, getDocumentsDir } from "@/src/lib/utils/invoke.utils";
import { toast } from "sonner";
import { Loader2Icon, CheckCircle2Icon } from "lucide-react";
import { Button } from "@/src/ui/button";
import { Card, CardDescription, CardHeader, CardTitle } from "@/src/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/src/components/ui/dialog";
import RestartButton from "../components/restartButton";
import { HOME } from "@/src/lib/utils/navigation.utils";

export function ButtonLoading() {
  return (
    <Button size="sm" disabled className="w-full justify-center space-x-2">
      <Loader2Icon className="animate-spin h-4 w-4" />
      <span>Please wait</span>
    </Button>
  );
}

export default function Page() {
  const router = useRouter();
  const pathname = usePathname();
  const step = getIndexByPathname(pathname);
  const [prevPath, ] = getNavigationByIndex(step);

  const [loading, setLoading] = useState(false);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [savedPath, setSavedPath] = useState("");

  const handleGenerateExcel = async () => {
    setLoading(true);
    try {
      const sel = localStorage.getItem("selectedMetrics");
      if (!sel) throw new Error("Aucune métrique sélectionnée");
      const metrics = JSON.parse(sel);

      const docsDir = await getDocumentsDir();
      const fileContent = await generateExcelFile(docsDir, metrics);

      const absPath = await save({
        defaultPath: "metrics_data.xlsx",
        filters: [{ name: "Excel", extensions: ["xlsx"] }],
      });
      if (!absPath) throw new Error("Enregistrement annulé");

      const relPath = absPath.replace(docsDir + "/", "");
      await writeFile(relPath, fileContent, { baseDir: BaseDirectory.Document });

      setSavedPath(absPath);
      setDialogOpen(true);
    } catch (e) {
      console.error(e);
      const message =
        typeof e === "object" && e !== null && "message" in e
          ? e.message
          : "Une erreur est survenue lors de l’export";
      toast.error(String(message));
    } finally {
      setLoading(false);
    }
  };

  const handleBack = () => prevPath && router.push(prevPath);

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
            <Button onClick={handleGenerateExcel} className="w-full cursor-pointer hover:rounded-lg hover:drop-shadow-md transition-all">
              Générer l&apos;Excel
            </Button>
          )}
        </Card>

        <div className="fixed bottom-4 left-0 right-0 px-6">
          <div className="flex justify-between">
            <BackButton onClick={handleBack} disable={!prevPath || loading} />
            <RestartButton onClick={() => router.push(HOME)} disable={loading} />
          </div>
        </div>
      </div>

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-w-md animate-fade-in scale-in origin-center">
          <DialogHeader className="text-center space-y-2">
            <DialogTitle>Téléchargement réussi</DialogTitle>
            <DialogDescription className="text-sm text-muted-foreground">
              Votre fichier a bien été enregistré sous :
              <br />
              <span className="font-mono break-all">{savedPath}</span>
            </DialogDescription>
            <CheckCircle2Icon className="mx-auto h-12 w-12 text-green-500" />
          </DialogHeader>
        </DialogContent>
      </Dialog>
    </>
  );
}
