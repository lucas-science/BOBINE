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
export type ChromeleonOnlinePermanentMetric = Metric & {
  chimicalElements?: string[];
};
export type PignatMetric = Metric & {
  columns: string[];
};

export type ResumeMetric = Metric;

export interface MetricsBySensor {
  chromeleon_offline: ChromeleonOfflineMetric[];
  chromeleon_online: ChromeleonOnlineMetric[];
  chromeleon_online_permanent_gas: ChromeleonOnlinePermanentMetric[];
  pignat: PignatMetric[];
  resume: ResumeMetric[];
}

// Time range selection for Pignat metrics
export interface TimeRangeSelection {
  startTime?: string;
  endTime?: string;
}

// Selected metrics to generate the excel file
export type MetricSelected = {
  name: string;
  chimicalElementSelected?: string[];
};

export type PignatSelectedMetric = {
  name: string;
  timeRange?: TimeRangeSelection;
};

export interface SelectedMetricsBySensor {
  chromeleon_offline: string[];
  chromeleon_online: MetricSelected[];
  chromeleon_online_permanent_gas: MetricSelected[];
  pignat: PignatSelectedMetric[];
  resume: string[];
}

export interface TimeRangeData {
  min_time: string;
  max_time: string;
  unique_times: string[];
}
