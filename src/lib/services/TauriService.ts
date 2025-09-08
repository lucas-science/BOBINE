import { invoke } from "@tauri-apps/api/core";
import { PyResp, SelectedMetricsBySensor, MetricsBySensor } from "../utils/type";

class TauriService {
  async getDocumentsDir(): Promise<string> {
    return await invoke<string>("get_documents_dir");
  }

  async checkContext(dirPath: string): Promise<boolean> {
    return await invoke<boolean>("context_is_correct", { dirPath });
  }

  async getContextMasses(dirPath: string): Promise<Record<string, number | null>> {
    return await invoke<Record<string, number | null>>("get_context_masses", { dirPath });
  }

  async getContextB64(dirPath: string): Promise<string> {
    return await invoke<string>("get_context_b64", { dirPath });
  }

  async getMetricsAvailable(dirPath: string): Promise<MetricsBySensor> {
    return await invoke<MetricsBySensor>("get_graphs_available", { dirPath });
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
}

export const tauriService = new TauriService();