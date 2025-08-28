export type PyResp = {
  result?: string;
  error?: string;
};

type Metric = {
  name: string;
  available: boolean;
};

export type ChromeleonOfflineMetric = Metric;
export type ChromeleonOnlineMetric = Metric & {
  chimicalElements?: string[];
};
export type PignaMetric = Metric & {
  columns: string[];
};

export interface MetricsBySensor {
  chromeleon_offline: ChromeleonOfflineMetric[];
  chromeleon_online: ChromeleonOnlineMetric[];
  pigna: PignaMetric[];
}

// Selected metrics to generate the excel file

export type MetricSelected = {
  name: string;
  chimicalElementSelected?: string[];
};
export interface SelectedMetricsBySensor {
  chromeleon_offline: string[];
  chromeleon_online: MetricSelected[];
  pigna: string[];
}
