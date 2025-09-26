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

// Error type for sensor initialization failures
export type SensorError = {
  error: string;
};

// Union type for sensor data: either array of metrics or error object
export type SensorMetrics<T> = T[] | SensorError;

// Type guard to check if sensor data is an error
export function isSensorError<T>(data: SensorMetrics<T>): data is SensorError {
  return typeof data === 'object' && data !== null && 'error' in data;
}

export interface MetricsBySensor {
  chromeleon_offline: SensorMetrics<ChromeleonOfflineMetric>;
  chromeleon_online: SensorMetrics<ChromeleonOnlineMetric>;
  chromeleon_online_permanent_gas: SensorMetrics<ChromeleonOnlinePermanentMetric>;
  pignat: SensorMetrics<PignatMetric>;
  resume: SensorMetrics<ResumeMetric>;
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

export interface ContextValidationResult {
  valid: boolean;
  error_type: "missing_experience_data" | "missing_masses" | "invalid_format" | "missing_directory" | null;
  error_message: string;
}
