import { invoke } from "@tauri-apps/api/core";
import { SelectedMetricsBySensor } from "./type";

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
): Promise<string> => {
  console.log('Generating Excel file with:', { dirPath, metrics });
  
  try {
    const result = await invoke<string>('generate_excel_file', {
      dirPath: dirPath,
      metricWanted: metrics
    });
    
    console.log('Excel generation result:', result);
    return result;
  } catch (error) {
    console.error('Erreur lors de la génération du fichier Excel:', error);
    
    // Essayer de parser l'erreur pour obtenir plus d'informations
    if (typeof error === 'string') {
      try {
        const errorObj = JSON.parse(error);
        console.error('Parsed error:', errorObj);
      } catch {
        console.error('Could not parse error as JSON:', error);
      }
    }
    
    throw error;
  }
};