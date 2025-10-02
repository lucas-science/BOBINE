import { invoke } from "@tauri-apps/api/core";
import { PyResp, SelectedMetricsBySensor, MetricsBySensor } from "../utils/type";

class TauriService {
  async getDocumentsDir(): Promise<string> {
    return await invoke<string>("get_documents_dir");
  }

  async checkContext(dirPath: string): Promise<boolean> {
    return await invoke<boolean>("context_is_correct", { dirPath });
  }

  async validateContext(dirPath: string): Promise<{valid: boolean; error_message: string}> {
    return await invoke<{valid: boolean; error_message: string}>("validate_context", { dirPath });
  }

  async getContextMasses(dirPath: string): Promise<Record<string, number | null>> {
    return await invoke<Record<string, number | null>>("get_context_masses", { dirPath });
  }

  async getContextB64(dirPath: string): Promise<string> {
    return await invoke<string>("get_context_b64", { dirPath });
  }

  async getContextExperienceName(dirPath: string): Promise<string> {
    return await invoke<string>("get_context_experience_name", { dirPath });
  }

  async getMetricsAvailable(dirPath: string): Promise<MetricsBySensor> {
    return await invoke<MetricsBySensor>("get_graphs_available", { dirPath });
  }

  async getTimeRange(dirPath: string): Promise<{
    min_time: string;
    max_time: string;
    unique_times: string[];
  }> {
    return await invoke("get_time_range", { dirPath });
  }

  async generateAndSaveExcel(
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

  async copyFile(sourcePath: string, destinationPath: string): Promise<void> {
    return await invoke("copy_file", { sourcePath, destinationPath });
  }

  async removeDir(dirPath: string): Promise<void> {
    return await invoke("remove_dir", { dirPath });
  }

  async writeFile(destinationPath: string, contents: number[]): Promise<void> {
    return await invoke("write_file", { destinationPath, contents });
  }
}

export const tauriService = new TauriService();