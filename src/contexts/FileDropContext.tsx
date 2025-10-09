"use client";
import React, { createContext, useContext, useState, useCallback, useRef } from "react";

interface FileDropContextType {
  activeZoneId: string | null;
  setActiveZoneId: (id: string | null) => void;
  registerZone: (id: string, element: HTMLElement) => void;
  unregisterZone: (id: string) => void;
}

const FileDropContext = createContext<FileDropContextType | null>(null);

export function FileDropProvider({ children }: { children: React.ReactNode }) {
  const [activeZoneId, setActiveZoneId] = useState<string | null>(null);
  const zonesRef = useRef<Map<string, HTMLElement>>(new Map());

  const registerZone = useCallback((id: string, element: HTMLElement) => {
    console.log(`[FileDropContext] Registering zone: ${id}`);
    zonesRef.current.set(id, element);
  }, []);

  const unregisterZone = useCallback((id: string) => {
    console.log(`[FileDropContext] Unregistering zone: ${id}`);
    zonesRef.current.delete(id);
  }, []);

  return (
    <FileDropContext.Provider value={{ activeZoneId, setActiveZoneId, registerZone, unregisterZone }}>
      {children}
    </FileDropContext.Provider>
  );
}

export function useFileDrop() {
  const context = useContext(FileDropContext);
  if (!context) {
    throw new Error("useFileDrop must be used within FileDropProvider");
  }
  return context;
}
