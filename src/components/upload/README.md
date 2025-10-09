# Upload Components Architecture

Clean, modular architecture for file upload components with drag-and-drop support.

## Structure

```
src/components/upload/
├── FileUploadZone.tsx      # Main container with drag-and-drop logic
├── FileUploadCard.tsx      # Card wrapper for zones
├── DragOverlay.tsx         # Visual animations during drag
├── FileList.tsx            # List of uploaded files
├── FileListItem.tsx        # Individual file item
├── UploadZoneError.tsx     # Error message display
├── LoaderOverlay.tsx       # Loading state overlay
├── ErrorAlert.tsx          # Alert component
└── index.ts                # Barrel exports

src/lib/utils/
├── fileHelpers.ts          # File icon & size formatting
├── tauriHelpers.ts         # Tauri environment detection & position checking
└── index.ts                # Barrel exports
```

## Components

### FileUploadZone (Main Component)

**Responsibility:** Orchestrates drag-and-drop functionality with Tauri integration

**Key Features:**
- Multi-zone drag-and-drop coordination
- Tauri 2.x event listeners with DPR correction
- HTML5 drag events fallback (dev mode)
- File validation and limits
- Position-based zone detection

**Props:**
```typescript
interface FileUploadZoneProps {
  description: string;
  onFileSelect: (files: File[]) => void;
  selectedFiles: File[];
  maxFiles: number;
}
```

**State Management:**
- `isDragOver`: Visual drag state
- `errorMessage`: Validation errors
- `dropZoneRef`: DOM reference for position checking
- `dragCounterRef`: HTML5 drag counter
- `activeZoneIdRef`: Active zone tracking

### DragOverlay

**Responsibility:** Animated visual feedback during drag

**Features:**
- Gradient glow animations
- Pulsing blue accent
- Animated dashed border (SVG)

### FileList

**Responsibility:** Display list of uploaded files

**Props:**
```typescript
interface FileListProps {
  files: File[];
  description: string;
  maxFiles: number;
  onRemoveFile: (index: number) => void;
}
```

**Features:**
- Limit indicator badge
- Scrollable list (max-height: 60)
- File count display

### FileListItem

**Responsibility:** Single file display with remove button

**Props:**
```typescript
interface FileListItemProps {
  file: File;
  onRemove: () => void;
}
```

**Features:**
- File type icon (image/video/text/generic)
- File size formatting
- Hover effects
- Remove button

### UploadZoneError

**Responsibility:** Display error messages

**Props:**
```typescript
interface UploadZoneErrorProps {
  message: string;
}
```

## Utilities

### fileHelpers.ts

**`getFileIcon(file: File)`**
- Returns appropriate Lucide icon component
- Detects: image, video, text/document, generic

**`formatFileSize(bytes: number)`**
- Human-readable file size
- Units: B, KB, MB, GB

### tauriHelpers.ts

**`isTauriEnv(): boolean`**
- Detects Tauri runtime
- Checks `__TAURI_INTERNALS__` and `__TAURI__`
- Type-safe window access

**`checkPositionOver(rect: DOMRect, position: {x, y}): boolean`**
- Check if cursor is over element
- Automatic DPR (Device Pixel Ratio) correction
- Handles high-DPI screens

## Drag-and-Drop Logic

### Tauri Mode (Production)
1. Listen to `onDragDropEvent` from webview
2. Check cursor position over zones
3. Apply DPR correction if needed
4. Convert file paths to File objects
5. Handle drop only in active zone

### HTML5 Mode (Dev Fallback)
1. Use standard HTML5 drag events
2. Counter-based enter/leave tracking
3. Direct File access from DataTransfer
4. Browser-only drag handling

## Critical Preservation

**DO NOT MODIFY:**
- All `useEffect` hooks (especially Tauri listeners)
- All `useRef` objects (`dropZoneRef`, `dragCounterRef`, `activeZoneIdRef`)
- Event handlers (`onDragEnter`, `onDragOver`, `onDragLeave`, `onDrop`)
- Position checking logic
- Cleanup logic (dev vs prod)

## Usage Example

```tsx
import { FileUploadZone } from '@/src/components/upload';

function MyComponent() {
  const [files, setFiles] = useState<File[]>([]);

  return (
    <FileUploadZone
      description="Context Files"
      selectedFiles={files}
      onFileSelect={setFiles}
      maxFiles={5}
    />
  );
}
```

## Benefits

✅ **Separation of Concerns:** Logic vs Presentation
✅ **Reusability:** Components can be used independently
✅ **Maintainability:** Clear file structure
✅ **Type Safety:** Full TypeScript support
✅ **Testability:** Pure components easy to test
✅ **Clean Imports:** Barrel exports (`from '@/src/components/upload'`)

## Performance

- `useCallback` for stable function references
- Conditional rendering (only render when needed)
- Optimized re-renders
- Cleanup in production only (avoid dev hot reload issues)
