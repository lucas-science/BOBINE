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
  const res = await invoke<{ stdout: string; stderr?: string }>(
    "run_python_script_with_dir",
    { dirPath, action: "GET_GRAPHS_AVAILABLE" }
  ).catch((e) => {
    // Erreur renvoyée par le Rust (stderr python)
    throw new Error(typeof e === "string" ? e : JSON.stringify(e));
  });

  if (!res || typeof res.stdout !== "string" || res.stdout.trim().length === 0) {
    throw new Error("Empty stdout from Python");
  }

  let parsed;
  try {
    parsed = JSON.parse(res.stdout);
  } catch (e) {
    console.error("Raw stdout:", res.stdout); // utile en dev
    throw e;
  }

  if (parsed?.error) {
    throw new Error(parsed.error);
  }

  // tu renvoies maintenant parsed.result (et plus l’objet brut)
  return parsed.result;
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