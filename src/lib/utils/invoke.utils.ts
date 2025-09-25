import { invoke } from "@tauri-apps/api/core";
import { PyResp, SelectedMetricsBySensor, ContextValidationResult } from "./type";
import { MetricsBySensor } from "./type";

export async function getDocumentsDir(): Promise<string> {
  return await invoke<string>("get_documents_dir");
}

export async function checkContext(dirPath: string): Promise<boolean> {
  return await invoke<boolean>("context_is_correct", { dirPath });
}

export async function validateContext(dirPath: string): Promise<ContextValidationResult> {
  return await invoke<ContextValidationResult>("validate_context", { dirPath });
}

export async function getContextMasses(dirPath: string): Promise<Record<string, number | null>> {
  return await invoke<Record<string, number | null>>("get_context_masses", { dirPath });
}

export async function getContextB64(dirPath: string): Promise<string> {
  return await invoke<string>("get_context_b64", { dirPath });
}
export async function getMetricsAvailable(dirPath: string): Promise<MetricsBySensor> {
  return await invoke<MetricsBySensor>("get_graphs_available", { dirPath });
}


export async function generateAndSaveExcel(
  dirPath: string,
  metrics: SelectedMetricsBySensor,
  destinationPath: string
): Promise<PyResp> {
  return await invoke<PyResp>("generate_and_save_excel", {
    dirPath,
    metricWanted: metrics,
    destinationPath,
  });
}


export async function copyFile(sourcePath: string, destinationPath: string): Promise<void> {
  return await invoke("copy_file", { sourcePath, destinationPath });
}