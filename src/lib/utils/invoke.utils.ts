import { invoke } from "@tauri-apps/api/core";

export async function checkContext(dirPath: string) {
  try {
    const response = await invoke('run_python_script', { action: 'CONTEXT_IS_CORRECT', dirPath,  });
    const parsedResponse = JSON.parse(response.stdout);
    return parsedResponse
  } catch (error) {
    console.error(error);
  }
}

export async function getMetricsAvailable(dirPath: string) {
  try {
    const response = await invoke('run_python_script', { action: 'GET_GRAPHS_AVAILABLE', dirPath });
    const parsedResponse = JSON.parse(response.stdout);
    return parsedResponse;
  } catch (error) {
    console.error(error);
  }
}
