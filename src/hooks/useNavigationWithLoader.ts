"use client";

import { useState, useEffect } from "react";
import { usePathname } from "next/navigation";

/**
 * Hook réutilisable pour gérer la navigation avec un overlay de loading
 *
 * @param targetPath - Le chemin de destination pour fermer automatiquement l'overlay
 * @returns objet avec overlayOpen, handleNavigateWithLoader et setOverlayOpen
 */
export const useNavigationWithLoader = (targetPath?: string) => {
  const [overlayOpen, setOverlayOpen] = useState(false);
  const pathname = usePathname();

  // Observer les changements de pathname pour fermer l'overlay automatiquement
  useEffect(() => {
    if (targetPath && pathname === targetPath && overlayOpen) {
      setOverlayOpen(false);
    }
  }, [pathname, targetPath, overlayOpen]);

  /**
   * Fonction pour naviguer avec un overlay de loading
   * Active l'overlay, exécute la fonction de navigation, puis l'overlay se ferme automatiquement
   *
   * @param navigationFn - Fonction de navigation à exécuter
   */
  const handleNavigateWithLoader = async (navigationFn: () => void | Promise<void>) => {
    setOverlayOpen(true);
    try {
      await navigationFn();
    } catch (error) {
      // En cas d'erreur, fermer l'overlay pour éviter qu'il reste bloqué
      setOverlayOpen(false);
      throw error;
    }
  };

  return {
    overlayOpen,
    handleNavigateWithLoader,
    setOverlayOpen
  };
};