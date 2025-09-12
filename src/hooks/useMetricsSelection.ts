"use client";

import {
  MetricsBySensor,
  SelectedMetricsBySensor,
  ChromeleonOfflineMetric,
  ChromeleonOnlineMetric,
  ChromeleonOnlinePermanentMetric,
  PignatMetric,
  ResumeMetric,
} from "@/src/lib/utils/type";

export const useMetricsSelection = (
  data: MetricsBySensor,
  onSelectionChange: (selected: SelectedMetricsBySensor) => void,
  setSelectedMetrics: React.Dispatch<React.SetStateAction<Set<string>>>,
  setOnlineElements: React.Dispatch<React.SetStateAction<Record<string, string[]>>>
) => {
  const buildSelectedFrom = (
    keys: Set<string>,
    onlineMap: Record<string, string[]>
  ): SelectedMetricsBySensor => {
    const out: SelectedMetricsBySensor = {
      chromeleon_offline: [],
      chromeleon_online: [],
      chromeleon_online_permanent_gas: [],
      pignat: [],
      resume: [],
    };

    keys.forEach((key) => {
      const [sensorType, indexStr] = key.split("-");
      const i = parseInt(indexStr, 10);

      if (sensorType === "chromeleon_offline") {
        const sensorData = data.chromeleon_offline;
        if (Array.isArray(sensorData)) {
          const m = sensorData[i] as ChromeleonOfflineMetric | undefined;
          if (m) out.chromeleon_offline.push(m.name);
        }
      } else if (sensorType === "pignat") {
        const sensorData = data.pignat;
        if (Array.isArray(sensorData)) {
          const m = sensorData[i] as PignatMetric | undefined;
          if (m) out.pignat.push({ name: m.name });
        }
      } else if (sensorType === "resume") {
        const sensorData = data.resume;
        if (Array.isArray(sensorData)) {
          const m = sensorData[i] as ResumeMetric | undefined;
          if (m) out.resume.push(m.name);
        }
      } else if (sensorType === "chromeleon_online") {
        const sensorData = data.chromeleon_online;
        if (Array.isArray(sensorData)) {
          const m = sensorData[i] as ChromeleonOnlineMetric | undefined;
          if (m) {
            const hasElements = Array.isArray(m.chimicalElements) && m.chimicalElements.length > 0;
            out.chromeleon_online.push({
              name: m.name,
              chimicalElementSelected: hasElements ? (onlineMap[key] ?? []) : [],
            });
          }
        }
      } else if (sensorType === "chromeleon_online_permanent_gas") {
        const sensorData = data.chromeleon_online_permanent_gas;
        if (Array.isArray(sensorData)) {
          const m = sensorData[i] as ChromeleonOnlinePermanentMetric | undefined;
          if (m) {
            const hasElements = Array.isArray(m.chimicalElements) && m.chimicalElements.length > 0;
            out.chromeleon_online_permanent_gas.push({
              name: m.name,
              chimicalElementSelected: hasElements ? (onlineMap[key] ?? []) : [],
            });
          }
        }
      }
    });

    return out;
  };

  const handleMetricToggle = (
    metricKey: string,
    available: boolean,
    selectedMetrics: Set<string>,
    onlineElements: Record<string, string[]>
  ) => {
    if (!available) return;
    const next = new Set(selectedMetrics);
    // eslint-disable-next-line @typescript-eslint/no-unused-expressions
    next.has(metricKey) ? next.delete(metricKey) : next.add(metricKey);
    setSelectedMetrics(next);
    onSelectionChange(buildSelectedFrom(next, onlineElements));
  };

  const addOnlineElement = (metricKey: string, value: string, selectedMetrics: Set<string>) => {
    setOnlineElements((prev) => {
      const cur = new Set(prev[metricKey] ?? []);
      cur.add(value);
      const nextMap = { ...prev, [metricKey]: Array.from(cur) };
      onSelectionChange(buildSelectedFrom(selectedMetrics, nextMap));
      return nextMap;
    });
  };

  const removeOnlineElement = (metricKey: string, value: string, selectedMetrics: Set<string>) => {
    setOnlineElements((prev) => {
      const cur = new Set(prev[metricKey] ?? []);
      cur.delete(value);
      const nextMap = { ...prev, [metricKey]: Array.from(cur) };
      onSelectionChange(buildSelectedFrom(selectedMetrics, nextMap));
      return nextMap;
    });
  };

  return {
    buildSelectedFrom,
    handleMetricToggle,
    addOnlineElement,
    removeOnlineElement,
  };
};