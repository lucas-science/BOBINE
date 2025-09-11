"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { tauriService } from "@/src/lib/services/TauriService";
import {
  MetricsBySensor,
  SelectedMetricsBySensor,
  TimeRangeSelection,
  TimeRangeData,
  ChromeleonOfflineMetric,
  ChromeleonOnlineMetric,
  ChromeleonOnlinePermanentMetric,
  PignatMetric,
  ResumeMetric,
  isSensorError,
} from "@/src/lib/utils/type";

export const useMetricsSelectionWithTimeRange = (
  data: MetricsBySensor,
  onSelectionChange: (selected: SelectedMetricsBySensor) => void
) => {
  const [selectedMetrics, setSelectedMetrics] = useState<Set<string>>(new Set());
  const [onlineElements, setOnlineElements] = useState<Record<string, string[]>>({});
  const [timeRanges, setTimeRanges] = useState<Record<string, TimeRangeSelection>>({});
  const [timeRangeData, setTimeRangeData] = useState<TimeRangeData | null>(null);
  const [isLoadingTimeRange, setIsLoadingTimeRange] = useState<boolean>(false);

  // Ref pour éviter la boucle infinie avec onSelectionChange
  const onSelectionChangeRef = useRef(onSelectionChange);
  onSelectionChangeRef.current = onSelectionChange;

  const buildSelectedFrom = useCallback((
    keys: Set<string>,
    onlineMap: Record<string, string[]>,
    timeRangeMap: Record<string, TimeRangeSelection>
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

      if (sensorType === "chromeleon_offline" && !isSensorError(data.chromeleon_offline)) {
        const m = data.chromeleon_offline?.[i] as ChromeleonOfflineMetric | undefined;
        if (m) out.chromeleon_offline.push(m.name);
      } else if (sensorType === "pignat" && !isSensorError(data.pignat)) {
        const m = data.pignat?.[i] as PignatMetric | undefined;
        if (m) {
          const globalTimeRange = timeRangeMap["pignat-global"];
          out.pignat.push({
            name: m.name,
            timeRange: globalTimeRange || undefined, // Envoie undefined si pas de plage sélectionnée
          });
        }
      } else if (sensorType === "resume" && !isSensorError(data.resume)) {
        const m = data.resume?.[i] as ResumeMetric | undefined;
        if (m) out.resume.push(m.name);
      } else if (sensorType === "chromeleon_online" && !isSensorError(data.chromeleon_online)) {
        const m = data.chromeleon_online?.[i] as ChromeleonOnlineMetric | undefined;
        if (m) {
          const hasElements = Array.isArray(m.chimicalElements) && m.chimicalElements.length > 0;
          out.chromeleon_online.push({
            name: m.name,
            chimicalElementSelected: hasElements ? (onlineMap[key] ?? []) : [],
          });
        }
      } else if (sensorType === "chromeleon_online_permanent_gas" && !isSensorError(data.chromeleon_online_permanent_gas)) {
        const m = data.chromeleon_online_permanent_gas?.[i] as ChromeleonOnlinePermanentMetric | undefined;
        if (m) {
          const hasElements = Array.isArray(m.chimicalElements) && m.chimicalElements.length > 0;
          out.chromeleon_online_permanent_gas.push({
            name: m.name,
            chimicalElementSelected: hasElements ? (onlineMap[key] ?? []) : [],
          });
        }
      }
    });

    return out;
  }, [data]);

  // Notifier les changements de sélection via useEffect pour éviter les setState pendant render
  useEffect(() => {
    onSelectionChangeRef.current(buildSelectedFrom(selectedMetrics, onlineElements, timeRanges));
  }, [selectedMetrics, onlineElements, timeRanges, buildSelectedFrom]);


  const loadTimeRangeData = async () => {
    if (timeRangeData || isLoadingTimeRange) return; // Éviter les appels multiples

    setIsLoadingTimeRange(true);
    try {
      const docsDir = await tauriService.getDocumentsDir();
      const timeRange = await tauriService.getTimeRange(docsDir);
      setTimeRangeData(timeRange);
    } catch (error) {
      console.error("Failed to load time range data:", error);
    } finally {
      setIsLoadingTimeRange(false);
    }
  };

  const handleMetricToggle = async (metricKey: string, available: boolean) => {
    if (!available) return;
    
    const next = new Set(selectedMetrics);
    const [sensorType] = metricKey.split("-");
    
    if (next.has(metricKey)) {
      next.delete(metricKey);
      
      // If this was a PIGNAT metric and no more PIGNAT metrics are selected, clean up global time range
      if (sensorType === "pignat") {
        const remainingPignatMetrics = Array.from(next).filter(key => key.startsWith("pignat-"));
        if (remainingPignatMetrics.length === 0) {
          const newTimeRanges = { ...timeRanges };
          delete newTimeRanges["pignat-global"];
          setTimeRanges(newTimeRanges);
        }
      }
    } else {
      next.add(metricKey);
      
      // If this is the first PIGNAT metric selected, load time range data
      if (sensorType === "pignat" && !timeRangeData && !isLoadingTimeRange) {
        await loadTimeRangeData();
      }
    }
    
    setSelectedMetrics(next);
  };

  const handleTimeRangeChange = (metricKey: string, timeRange: TimeRangeSelection) => {
    const newTimeRanges = { ...timeRanges, [metricKey]: timeRange };
    setTimeRanges(newTimeRanges);
  };

  const addOnlineElement = (metricKey: string, value: string) => {
    setOnlineElements((prev) => {
      const cur = new Set(prev[metricKey] ?? []);
      cur.add(value);
      const nextMap = { ...prev, [metricKey]: Array.from(cur) };
      return nextMap;
    });
  };

  const removeOnlineElement = (metricKey: string, value: string) => {
    setOnlineElements((prev) => {
      const cur = new Set(prev[metricKey] ?? []);
      cur.delete(value);
      const nextMap = { ...prev, [metricKey]: Array.from(cur) };
      return nextMap;
    });
  };

  const getAllAvailableMetrics = () => {
    const availableMetrics: string[] = [];
    
    // Chromeleon Offline
    if (!isSensorError(data.chromeleon_offline)) {
      data.chromeleon_offline?.forEach((metric, index) => {
        if (metric.available) {
          availableMetrics.push(`chromeleon_offline-${index}`);
        }
      });
    }
    
    // Chromeleon Online
    if (!isSensorError(data.chromeleon_online)) {
      data.chromeleon_online?.forEach((metric, index) => {
        if (metric.available) {
          availableMetrics.push(`chromeleon_online-${index}`);
        }
      });
    }
    
    // Chromeleon Online Permanent Gas
    if (!isSensorError(data.chromeleon_online_permanent_gas)) {
      data.chromeleon_online_permanent_gas?.forEach((metric, index) => {
        if (metric.available) {
          availableMetrics.push(`chromeleon_online_permanent_gas-${index}`);
        }
      });
    }
    
    // PIGNAT
    if (!isSensorError(data.pignat)) {
      data.pignat?.forEach((metric, index) => {
        if (metric.available) {
          availableMetrics.push(`pignat-${index}`);
        }
      });
    }
    
    // Resume
    if (!isSensorError(data.resume)) {
      data.resume?.forEach((metric, index) => {
        if (metric.available) {
          availableMetrics.push(`resume-${index}`);
        }
      });
    }
    
    return availableMetrics;
  };

  const selectAll = async () => {
    const availableMetrics = getAllAvailableMetrics();
    const newSelection = new Set(availableMetrics);
    
    // Si on sélectionne des métriques PIGNAT et qu'on n'a pas encore les timeRangeData
    const hasPignatMetrics = availableMetrics.some(key => key.startsWith("pignat-"));
    if (hasPignatMetrics && !timeRangeData && !isLoadingTimeRange) {
      await loadTimeRangeData();
    }
    
    setSelectedMetrics(newSelection);
  };

  const deselectAll = () => {
    const newSelection = new Set<string>();
    const newTimeRanges = { ...timeRanges };
    delete newTimeRanges["pignat-global"];
    
    setSelectedMetrics(newSelection);
    setTimeRanges(newTimeRanges);
  };

  const isAllSelected = () => {
    const availableMetrics = getAllAvailableMetrics();
    return availableMetrics.length > 0 && availableMetrics.every(key => selectedMetrics.has(key));
  };

  return {
    selectedMetrics,
    onlineElements,
    timeRanges,
    timeRangeData,
    isLoadingTimeRange,
    handleMetricToggle,
    handleTimeRangeChange,
    addOnlineElement,
    removeOnlineElement,
    selectAll,
    deselectAll,
    isAllSelected,
  };
};