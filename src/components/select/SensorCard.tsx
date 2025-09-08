"use client";

import React from "react";
import { Card } from "@/src/components/ui/card";
import { MetricsSection } from "./MetricsSection";
import { MetricItem } from "./MetricItem";
import { ChromeleonOnlineItem } from "./chromeleonOnlineItem";
import {
  ChromeleonOfflineMetric,
  ChromeleonOnlineMetric,
  ChromeleonOnlinePermanentMetric,
  PignatMetric,
  ResumeMetric,
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
}

export const SensorCard: React.FC<SensorCardProps> = ({
  sensorType,
  data,
  selectedMetrics,
  onlineElements,
  onMetricToggle,
  onAddElement,
  onRemoveElement,
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
          name={pignatMetric.name}
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
        name={metric.name}
        available={metric.available}
        selected={isSelected}
        onToggle={() => onMetricToggle(metricKey, metric.available)}
      />
    );
  };

  return (
    <Card className="shadow-sm">
      <MetricsSection title={SENSOR_DISPLAY_NAMES[sensorType]}>
        {data.map((metric, index) => renderMetricItem(metric, index))}
      </MetricsSection>
    </Card>
  );
};