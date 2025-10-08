import { readFile } from '@tauri-apps/plugin-fs';

/**
 * Converts file paths to File objects using Tauri's fs plugin
 * @param paths - Array of absolute file paths
 * @returns Promise resolving to an array of File objects
 */
export async function pathsToFiles(paths: string[]): Promise<File[]> {
  const filePromises = paths.map(async (path) => {
    try {
      // Extract filename from path
      const fileName = path.split(/[\\/]/).pop() || 'unknown';

      // Read file content as binary
      const contents = await readFile(path);

      // Detect MIME type based on extension
      const extension = fileName.split('.').pop()?.toLowerCase() || '';
      const mimeType = getMimeType(extension);

      // Create Blob from Uint8Array
      const blob = new Blob([contents], { type: mimeType });

      // Create File object
      const file = new File([blob], fileName, { type: mimeType });

      return file;
    } catch (error) {
      console.error(`Failed to read file at path: ${path}`, error);
      throw new Error(`Unable to read file: ${path}`);
    }
  });

  return Promise.all(filePromises);
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
