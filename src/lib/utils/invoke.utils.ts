import { invoke } from "@tauri-apps/api/core";
import { SelectedMetricsBySensor } from "./type";
import { MetricsBySensor } from "./type";

export async function getDocumentsDir(): Promise<string> {
  return await invoke<string>("get_documents_dir");
}

export async function checkContext(dirPath: string): Promise<boolean> {
  return await invoke<boolean>("context_is_correct", { dirPath });
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


export const generateExcelFile = async (
  dirPath: string,
  metrics: SelectedMetricsBySensor
): Promise<Uint8Array> => {
  const bytesArray = await invoke<number[]>("generate_excel_file", {
    dirPath,
    metricWanted: metrics,
  });
  return new Uint8Array(bytesArray);
};