import { invoke } from "@tauri-apps/api/core";
import { SelectedMetricsBySensor } from "./type";

export async function getDocumentsDir(): Promise<string> {
  return await invoke<string>("get_documents_dir");
}

export async function checkContext(dirPath: string): Promise<boolean> {
  return await invoke<boolean>("context_is_correct", { dirPath });
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