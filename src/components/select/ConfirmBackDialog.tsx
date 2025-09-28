"use client";

import React from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/src/components/ui/dialog";
import { Button } from "@/src/ui/button";

type ConfirmBackDialogProps = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onConfirm: () => void;
};

export function ConfirmBackDialog({ open, onOpenChange, onConfirm }: ConfirmBackDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Confirmer le retour</DialogTitle>
          <DialogDescription>
            Voulez vous vraiment revenir à la page de sélection des fichier, si oui, vous devrez réimporter manuellement chaque fichier.
          </DialogDescription>
        </DialogHeader>

        <DialogFooter className="gap-2">
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
            className="cursor-pointer"
          >
            Annuler
          </Button>
          <Button
            variant="destructive"
            onClick={onConfirm}
            className="cursor-pointer"
          >
            Revenir à l&apos;accueil
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}