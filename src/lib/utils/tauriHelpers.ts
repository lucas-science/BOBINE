// Type for Tauri global window object
interface TauriWindow extends Window {
  __TAURI_INTERNALS__?: unknown;
  __TAURI__?: unknown;
}

/**
 * Check if running in Tauri environment
 */
export const isTauriEnv = (): boolean => {
  if (typeof window === 'undefined') return false;
  const w = window as TauriWindow;
  return !!(w.__TAURI_INTERNALS__ || w.__TAURI__);
};

/**
 * Check if a position is over a DOM element
 * Handles DPR (Device Pixel Ratio) correction for high-DPI screens
 */
export const checkPositionOver = (
  rect: DOMRect,
  position: { x: number; y: number }
): boolean => {
  let x = position.x;
  let y = position.y;
  let isOver = (x >= rect.left && x <= rect.right && y >= rect.top && y <= rect.bottom);

  // Try with DPR correction if not over (for high-DPI screens)
  if (!isOver) {
    const dpr = window.devicePixelRatio || 1;
    x = position.x / dpr;
    y = position.y / dpr;
    isOver = (x >= rect.left && x <= rect.right && y >= rect.top && y <= rect.bottom);
  }

  return isOver;
};
