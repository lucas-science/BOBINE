import { readFile } from '@tauri-apps/plugin-fs';

/**
 * Converts file paths to File objects using Tauri's fs plugin
 * @param paths - Array of absolute file paths
 * @returns Promise resolving to an array of File objects
 */
export async function pathsToFiles(paths: string[]): Promise<File[]> {
  console.log(`[pathsToFiles] Converting ${paths.length} paths to File objects:`, paths);

  const filePromises = paths.map(async (path, index) => {
    try {
      console.log(`[pathsToFiles] [${index + 1}/${paths.length}] Processing: ${path}`);

      // Extract filename from path
      const fileName = path.split(/[\\/]/).pop() || 'unknown';
      console.log(`[pathsToFiles] [${index + 1}/${paths.length}] Filename: ${fileName}`);

      // Read file content as binary
      console.log(`[pathsToFiles] [${index + 1}/${paths.length}] Reading file content...`);
      const contents = await readFile(path);
      console.log(`[pathsToFiles] [${index + 1}/${paths.length}] Read ${contents.byteLength} bytes`);

      // Detect MIME type based on extension
      const extension = fileName.split('.').pop()?.toLowerCase() || '';
      const mimeType = getMimeType(extension);
      console.log(`[pathsToFiles] [${index + 1}/${paths.length}] MIME type: ${mimeType} (extension: ${extension})`);

      // Create Blob from Uint8Array
      const blob = new Blob([contents], { type: mimeType });

      // Create File object
      const file = new File([blob], fileName, { type: mimeType });
      console.log(`[pathsToFiles] ✅ [${index + 1}/${paths.length}] Created File object:`, {
        name: file.name,
        size: file.size,
        type: file.type
      });

      return file;
    } catch (error) {
      console.error(`[pathsToFiles] ❌ Failed to read file at path: ${path}`, error);
      throw new Error(`Unable to read file: ${path}`);
    }
  });

  const results = await Promise.all(filePromises);
  console.log(`[pathsToFiles] ✅ Successfully converted all ${results.length} files`);
  return results;
}

/**
 * Get MIME type based on file extension
 * @param extension - File extension (without dot)
 * @returns MIME type string
 */
function getMimeType(extension: string): string {
  const mimeTypes: Record<string, string> = {
    // Text files
    txt: 'text/plain',
    csv: 'text/csv',

    // Excel files
    xls: 'application/vnd.ms-excel',
    xlsx: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',

    // Document files
    pdf: 'application/pdf',
    doc: 'application/msword',
    docx: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',

    // Data files
    json: 'application/json',
    xml: 'application/xml',

    // Archive files
    zip: 'application/zip',
    rar: 'application/x-rar-compressed',

    // Image files
    png: 'image/png',
    jpg: 'image/jpeg',
    jpeg: 'image/jpeg',
    gif: 'image/gif',
    svg: 'image/svg+xml',

    // Video files
    mp4: 'video/mp4',
    avi: 'video/x-msvideo',

    // Audio files
    mp3: 'audio/mpeg',
    wav: 'audio/wav',
  };

  return mimeTypes[extension] || 'application/octet-stream';
}
