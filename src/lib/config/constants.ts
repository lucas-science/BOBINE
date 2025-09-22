export const SENSOR_DISPLAY_NAMES = {
  chromeleon_offline: "Chromeleon Offline",
  chromeleon_online: "Chromeleon Online",
  chromeleon_online_permanent_gas: "Chromeleon online Permanent Gas",
  pignat: "Pignat",
  resume: "Resume",
} as const;

export const STORAGE_KEYS = {
  SELECTED_METRICS: "selectedMetrics",
} as const;

export const BOBINE_DATA_FOLDER = "Bobine_data" as const;

export const API_ENDPOINTS = {
  GET_DOCUMENTS_DIR: "get_documents_dir",
  CONTEXT_IS_CORRECT: "context_is_correct",
  GET_CONTEXT_MASSES: "get_context_masses",
  GET_CONTEXT_B64: "get_context_b64",
  GET_GRAPHS_AVAILABLE: "get_graphs_available",
  GENERATE_AND_SAVE_EXCEL: "generate_and_save_excel",
  COPY_FILE: "copy_file",
} as const;