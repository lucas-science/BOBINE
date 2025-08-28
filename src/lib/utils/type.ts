export type PyResp = { result?: string; error?: string };

export type Metric = {
  name: string;
  columns?: string[];
  available: boolean;
}

export interface MetricsBySensor {
  chromeleon_offline: Metric[];
  chromeleon_online: Metric[];
  pigna: Metric[];
}

export interface SelectedMetricsBySensor {
  chromeleon_offline: string[];
  chromeleon_online: string[];
  pigna: string[];
}
