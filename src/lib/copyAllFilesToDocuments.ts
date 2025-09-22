import { invoke } from "@tauri-apps/api/core";
import { FILE_ZONE } from "@/src/lib/utils/uploadFile.utils";
import { BOBINE_DATA_FOLDER } from "@/src/lib/config/constants";
import type { FilesByZoneKey } from "@/src/hooks/useUploadState";

export async function copyAllFilesToDocuments(allFilesByZoneKey: FilesByZoneKey) {
  try {
    const docsDir: string = await invoke("get_documents_dir");

    // reset des répertoires racine de chaque zone
    for (const zoneKey of Object.keys(FILE_ZONE)) {
      await invoke("remove_dir", { dirPath: `${docsDir}/${BOBINE_DATA_FOLDER}/${zoneKey}` });
    }

    for (const [zoneKey, zoneFilesArray] of Object.entries(allFilesByZoneKey)) {
      const zoneDefs = FILE_ZONE[zoneKey as keyof typeof FILE_ZONE];
      if (!zoneDefs) continue;

      for (let zoneIndex = 0; zoneIndex < zoneDefs.length; zoneIndex++) {
        const files = (zoneFilesArray as Array<Array<File>>)[zoneIndex] || [];
        const zoneName = zoneDefs[zoneIndex].zone;
        const zonePath = `${docsDir}/${BOBINE_DATA_FOLDER}/${zoneKey}/${zoneName}`;

        for (const file of files) {
          const destName = `${zoneKey}_${zoneName}_${Date.now()}_${file.name}`;
          const destPath = `${zonePath}/${destName}`;
          const buffer = await file.arrayBuffer();
          const arr = Array.from(new Uint8Array(buffer));
          await invoke("write_file", { destinationPath: destPath, contents: arr });
        }
      }
    }
    return true;
  } catch (err) {
    console.error("❌ Erreur de copie :", err);
    return false;
  }
}
