import { FILE_ZONE } from "@/src/lib/utils/uploadFile.utils";
import { BOBINE_DATA_FOLDER } from "@/src/lib/config/constants";
import { tauriService } from "@/src/lib/services/TauriService";
import type { FilesByZoneKey } from "@/src/hooks/useUploadState";

// Mapping des clés UI vers les chemins backend pour maintenir la compatibilité Python
const ZONE_KEY_TO_BACKEND_PATH: Record<string, string> = {
  context: "context",
  pignat: "pignat",
  gc_online: "chromeleon",
  gc_offline: "chromeleon",
};

export async function copyAllFilesToDocuments(allFilesByZoneKey: FilesByZoneKey) {
  try {
    const docsDir = await tauriService.getDocumentsDir();

    // reset des répertoires racine backend (dédupliqués)
    const backendPaths = new Set(Object.values(ZONE_KEY_TO_BACKEND_PATH));
    for (const backendPath of backendPaths) {
      await tauriService.removeDir(`${docsDir}/${BOBINE_DATA_FOLDER}/${backendPath}`);
    }
    // reset aussi chromeleon_online_permanent_gas (cas spécial)
    await tauriService.removeDir(`${docsDir}/${BOBINE_DATA_FOLDER}/chromeleon_online_permanent_gas`);

    for (const [zoneKey, zoneFilesArray] of Object.entries(allFilesByZoneKey)) {
      const zoneDefs = FILE_ZONE[zoneKey as keyof typeof FILE_ZONE];
      if (!zoneDefs) continue;

      const backendPath = ZONE_KEY_TO_BACKEND_PATH[zoneKey] || zoneKey;

      for (let zoneIndex = 0; zoneIndex < zoneDefs.length; zoneIndex++) {
        const files = (zoneFilesArray as Array<Array<File>>)[zoneIndex] || [];
        const zoneName = zoneDefs[zoneIndex].zone;

        // Gérer le cas spécial de chromeleon_online_permanent_gas
        const actualBackendPath = zoneName === "chromeleon_online_permanent_gas"
          ? "chromeleon_online_permanent_gas"
          : backendPath;

        const zonePath = `${docsDir}/${BOBINE_DATA_FOLDER}/${actualBackendPath}/${zoneName}`;

        for (const file of files) {
          const destName = `${actualBackendPath}_${zoneName}_${Date.now()}_${file.name}`;
          const destPath = `${zonePath}/${destName}`;
          const buffer = await file.arrayBuffer();
          const arr = Array.from(new Uint8Array(buffer));
          await tauriService.writeFile(destPath, arr);
        }
      }
    }
    return true;
  } catch (err) {
    console.error("❌ Erreur de copie :", err);
    return false;
  }
}
