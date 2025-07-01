import { invoke } from "@tauri-apps/api/core";

export async function checkContext(dirPath: string) {
  try {
    const response = await invoke('run_python_script', { dirPath, action: 'CONTEXT_IS_CORRECT' });
    const parsedResponse = JSON.parse(response.stdout);
    return parsedResponse
  } catch (error) {
    console.error(error);
  }
}

export async function getMetricsAvailable(dirPath: string) {
  try {
    const response = await invoke('run_python_script', { dirPath, action: 'GET_GRAPHS_AVAILABLE' });
    const parsedResponse = JSON.parse(response.stdout);
    return parsedResponse;
  } catch (error) {
    console.error(error);
  }
}
