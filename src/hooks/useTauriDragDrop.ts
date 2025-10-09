import { useEffect, RefObject } from 'react';
import { getCurrentWebviewWindow } from '@tauri-apps/api/webviewWindow';
import { pathsToFiles } from '@/src/lib/fileUtils';
import { isTauriEnv, checkPositionOver } from '@/src/lib/utils/tauriHelpers';

interface UseTauriDragDropOptions {
  zoneId: string;
  description: string;
  isAtLimit: boolean;
  dropZoneRef: RefObject<HTMLDivElement | null>;
  activeZoneIdRef: RefObject<string | null>;
  dragCounterRef: RefObject<number>;
  setIsDragOver: (value: boolean) => void;
  setActiveZoneId: (id: string | null) => void;
  handleNewFiles: (files: File[]) => void;
  resetDragState: () => void;
  onError?: (message: string) => void;
}

/**
 * Custom hook to handle Tauri drag-and-drop events
 * Sets up listeners for file drop events with position-based zone detection
 */
export function useTauriDragDrop({
  zoneId,
  description,
  isAtLimit,
  dropZoneRef,
  activeZoneIdRef,
  dragCounterRef,
  setIsDragOver,
  setActiveZoneId,
  handleNewFiles,
  resetDragState,
  onError,
}: UseTauriDragDropOptions) {
  useEffect(() => {
    let unlistenDrop: (() => void) | undefined;
    let isMounted = true;
    let isListenerRegistered = false;

    const setupListeners = async () => {
      try {
        if (!isTauriEnv()) return;

        const appWebview = getCurrentWebviewWindow();
        if (!appWebview) return;

        const unlisten = await appWebview.onDragDropEvent(async (event) => {
          if (!isMounted) return;

          const payload = event.payload as {
            type: string;
            position?: { x: number; y: number };
            paths?: string[];
          };
          const { type, position, paths } = payload;

          if (type === "enter" || type === "over") {
            if (dropZoneRef.current && position) {
              const rect = dropZoneRef.current.getBoundingClientRect();
              const isOver = checkPositionOver(rect, position);

              if (isOver && !isAtLimit) {
                setIsDragOver(true);
                setActiveZoneId(zoneId);
                activeZoneIdRef.current = zoneId;
                dragCounterRef.current = 1;
              } else if (activeZoneIdRef.current === zoneId && !isOver) {
                resetDragState();
              }
            }
          } else if (type === "drop") {
            if (activeZoneIdRef.current === zoneId && paths?.length) {
              try {
                const files = await pathsToFiles(paths);
                handleNewFiles(files);
              } catch (error) {
                console.error(`[useTauriDragDrop ${description}] Error converting files:`, error);
                onError?.("Erreur lors de la lecture des fichiers.");
              }
            }
            resetDragState();
          } else if (type === "leave") {
            if (activeZoneIdRef.current === zoneId) {
              resetDragState();
            }
          } else if (type === "cancel") {
            resetDragState();
          }
        });

        if (unlisten && typeof unlisten === 'function' && isMounted) {
          unlistenDrop = unlisten;
          isListenerRegistered = true;
        }
        // If component unmounted during setup, don't call unlisten
        // Tauri will handle cleanup automatically when window closes
      } catch (error) {
        console.error(`[useTauriDragDrop ${description}] Failed to setup Tauri listeners:`, error);
      }
    };

    setupListeners();

    // Cleanup function
    return () => {
      isMounted = false;

      // Skip all cleanup in development to avoid hot reload issues
      if (process.env.NODE_ENV === 'development') {
        return;
      }

      // Production cleanup only
      if (isListenerRegistered && unlistenDrop) {
        setTimeout(() => {
          try {
            if (typeof unlistenDrop === 'function' && isTauriEnv()) {
              unlistenDrop();
            }
          } catch {
            // Silently ignore cleanup errors
          }
        }, 0);
      }
    };
  }, [
    zoneId,
    description,
    isAtLimit,
    dropZoneRef,
    activeZoneIdRef,
    dragCounterRef,
    setIsDragOver,
    setActiveZoneId,
    handleNewFiles,
    resetDragState,
    onError,
  ]);
}
