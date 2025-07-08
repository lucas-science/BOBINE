import { invoke } from "@tauri-apps/api/core";
import { SelectedMetricsBySensor } from "./type";

export async function getDocumentsDir(): Promise<string> {
  return await invoke<string>("get_documents_dir");
}

export async function checkContext(dirPath: string) {
  try {
    const response = await invoke('run_python_script_with_dir', { 
      dirPath: dirPath,
      action: 'CONTEXT_IS_CORRECT'
    });
    
    console.log('Response from Python script:', response);
    const parsedResponse = JSON.parse(response.stdout);
    return parsedResponse;
  } catch (error) {
    console.error(error);
    throw error;
  }
}

export async function getMetricsAvailable(dirPath: string) {
  try {
    const response = await invoke('run_python_script_with_dir', { 
      dirPath: dirPath,
      action: 'GET_GRAPHS_AVAILABLE'
    });
    
    const parsedResponse = JSON.parse(response.stdout);
    return parsedResponse;
  } catch (error) {
    console.error(error);
    throw error;
  }
}

export const generateExcelFile = async (
  dirPath: string,
  metrics: SelectedMetricsBySensor
): Promise<Uint8Array> => {
  try {
    // On attend un array de nombres, pas un { data: string }
    const bytesArray = await invoke<number[]>("generate_excel_file", {
      dirPath,
      metricWanted: metrics
    });
    // On convertit directement en Uint8Array
    return new Uint8Array(bytesArray);
  } catch (e) {
    console.error("Error generating Excel file:", e);
    throw e;
  }
};