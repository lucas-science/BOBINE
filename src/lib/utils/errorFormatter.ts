/**
 * Error formatting utilities for development debugging
 */

export interface ErrorDetails {
  timestamp: string;
  message: string;
  stack?: string;
  backendError?: string;
  rawError?: unknown;
}

/**
 * Parse and structure an error for debugging purposes
 */
export function parseError(error: unknown, backendError?: string): ErrorDetails {
  const timestamp = new Date().toISOString();

  if (error instanceof Error) {
    return {
      timestamp,
      message: error.message,
      stack: error.stack,
      backendError,
      rawError: error,
    };
  }

  return {
    timestamp,
    message: typeof error === 'string' ? error : 'Unknown error',
    backendError,
    rawError: error,
  };
}

/**
 * Format error details as a readable string for clipboard
 */
export function formatErrorForClipboard(details: ErrorDetails): string {
  const sections: string[] = [
    `=== ERROR DEBUG INFO ===`,
    `Timestamp: ${details.timestamp}`,
    ``,
    `--- Frontend Error ---`,
    `Message: ${details.message}`,
  ];

  if (details.stack) {
    sections.push(``, `Stack Trace:`, details.stack);
  }

  if (details.backendError) {
    sections.push(
      ``,
      `--- Backend Error ---`,
      details.backendError
    );
  }

  if (details.rawError) {
    sections.push(
      ``,
      `--- Raw Error Object ---`,
      JSON.stringify(details.rawError, null, 2)
    );
  }

  return sections.join('\n');
}

/**
 * Copy error details to clipboard
 */
export async function copyErrorToClipboard(details: ErrorDetails): Promise<boolean> {
  try {
    const text = formatErrorForClipboard(details);
    await navigator.clipboard.writeText(text);
    return true;
  } catch (err) {
    console.error('Failed to copy to clipboard:', err);
    return false;
  }
}
