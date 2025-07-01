export type Metric = {
  name: string;
  columns: string[];
  available: boolean;
}

export interface MetricsBySensor {
  chromeleon_offline: Metric[];
  chromeleon_online: Metric[];
  pigna: Metric[];
}
