"use client";

import React from "react";
import { Card } from "@/src/components/ui/card";
import { MetricsSection } from "./MetricsSection";
import { MetricItem } from "./MetricItem";
import { ChromeleonOnlineItem } from "./chromeleonOnlineItem";
import { TimeRangeSelector } from "./TimeRangeSelector";
import {
  ChromeleonOfflineMetric,
  ChromeleonOnlineMetric,
  ChromeleonOnlinePermanentMetric,
  PignatMetric,
  ResumeMetric,
  TimeRangeSelection,
  TimeRangeData,
} from "@/src/lib/utils/type";
import { SENSOR_DISPLAY_NAMES } from "@/src/lib/config/constants";

type SensorType = "chromeleon_offline" | "chromeleon_online" | "chromeleon_online_permanent_gas" | "pignat" | "resume";
type MetricData = ChromeleonOfflineMetric | ChromeleonOnlineMetric | ChromeleonOnlinePermanentMetric | PignatMetric | ResumeMetric;

interface SensorCardProps {
  sensorType: SensorType;
  data: MetricData[];
  selectedMetrics: Set<string>;
  onlineElements: Record<string, string[]>;
  onMetricToggle: (metricKey: string, available: boolean) => void;
  onAddElement: (metricKey: string, value: string) => void;
  onRemoveElement: (metricKey: string, value: string) => void;
  // Optional props for Pignat time range selection
  timeRanges?: Record<string, TimeRangeSelection>;
  timeRangeData?: TimeRangeData | null;
  isLoadingTimeRange?: boolean;
  onTimeRangeChange?: (metricKey: string, timeRange: TimeRangeSelection) => void;
}

export const SensorCard: React.FC<SensorCardProps> = ({
  sensorType,
  data,
  selectedMetrics,
  onlineElements,
  onMetricToggle,
  onAddElement,
  onRemoveElement,
  timeRanges,
  timeRangeData,
  isLoadingTimeRange = false,
  onTimeRangeChange,
}) => {
  const renderMetricItem = (metric: MetricData, index: number) => {
    const metricKey = `${sensorType}-${index}`;
    const isSelected = selectedMetrics.has(metricKey);

    if (sensorType === "chromeleon_online" || sensorType === "chromeleon_online_permanent_gas") {
      const onlineMetric = metric as ChromeleonOnlineMetric | ChromeleonOnlinePermanentMetric;
      const hasElements = Array.isArray(onlineMetric.chimicalElements) && onlineMetric.chimicalElements.length > 0;

      if (!hasElements) {
        return (
          <MetricItem
            key={metricKey}
            metricKey={metricKey}
            name={onlineMetric.name}
            available={onlineMetric.available}
            selected={isSelected}
            onToggle={() => onMetricToggle(metricKey, onlineMetric.available)}
          />
        );
      }

      const chosen = onlineElements[metricKey] ?? [];
      return (
        <ChromeleonOnlineItem
          key={metricKey}
          metricKey={metricKey}
          name={onlineMetric.name}
          available={onlineMetric.available}
          selected={isSelected}
          chimicalElements={onlineMetric.chimicalElements ?? []}
          chosenElements={chosen}
          onToggle={() => onMetricToggle(metricKey, onlineMetric.available)}
          onAddElement={(v: string) => onAddElement(metricKey, v)}
          onRemoveElement={(v: string) => onRemoveElement(metricKey, v)}
        />
      );
    }

    if (sensorType === "pignat") {
      const pignatMetric = metric as PignatMetric;
      return (
        <MetricItem
          key={metricKey}
          metricKey={metricKey}
          name={pignatMetric.displayName || pignatMetric.name}
          available={pignatMetric.available}
          selected={isSelected}
          onToggle={() => onMetricToggle(metricKey, pignatMetric.available)}
          subText={
            pignatMetric.columns?.length ? `Colonnes: ${pignatMetric.columns.join(", ")}` : undefined
          }
        />
      );
    }

    return (
      <MetricItem
        key={metricKey}
        metricKey={metricKey}
        name={metric.displayName || metric.name}
        available={metric.available}
        selected={isSelected}
        onToggle={() => onMetricToggle(metricKey, metric.available)}
      />
    );
  };

  const hasSelectedPignatMetrics = sensorType === "pignat" && 
    data.some((_, index) => selectedMetrics.has(`${sensorType}-${index}`));

  return (
    <Card className="shadow-sm">
      <MetricsSection title={SENSOR_DISPLAY_NAMES[sensorType]}>
        {data.map((metric, index) => renderMetricItem(metric, index))}
        {hasSelectedPignatMetrics && onTimeRangeChange && (
          <div className="mt-4 pt-3 border-t border-gray-200">
            {isLoadingTimeRange ? (
              <div className="flex items-center justify-center p-4 text-sm text-gray-500">
                <div className="animate-spin rounded-full h-4 w-4 border-2 border-gray-300 border-t-blue-600 mr-2"></div>
                Chargement des plages temporelles...
              </div>
            ) : timeRangeData ? (
              <TimeRangeSelector
                availableTimes={timeRangeData.unique_times}
                selectedRange={timeRanges?.["pignat-global"]}
                onRangeChange={(range) => onTimeRangeChange("pignat-global", range)}
                disabled={false}
              />
            ) : (
              <div className="text-sm text-gray-500 italic p-2">
                Aucune donnée temporelle disponible
              </div>
            )}
          </div>
        )}
      </MetricsSection>
    </Card>
  );
};