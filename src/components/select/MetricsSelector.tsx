"use client";

import React, { useState } from "react";
import { MetricsBySensor, SelectedMetricsBySensor } from "@/src/lib/utils/type";
import { SensorCard } from "./SensorCard";
import { useMetricsSelection } from "@/src/hooks/useMetricsSelection";

interface MetricsSelectorProps {
  data: MetricsBySensor;
  onSelectionChange: (selected: SelectedMetricsBySensor) => void;
  className?: string;
}

export const MetricsSelector: React.FC<MetricsSelectorProps> = ({
  data,
  onSelectionChange,
  className = "",
}) => {
  const [selectedMetrics, setSelectedMetrics] = useState<Set<string>>(new Set());
  const [onlineElements, setOnlineElements] = useState<Record<string, string[]>>({});

  const {
    buildSelectedFrom,
    handleMetricToggle,
    addOnlineElement,
    removeOnlineElement,
  } = useMetricsSelection(data, onSelectionChange, setSelectedMetrics, setOnlineElements);

  return (
    <div className={`w-full max-w-2xl mx-auto space-y-4 ${className}`}>
      <SensorCard
        sensorType="chromeleon_offline"
        data={data.chromeleon_offline}
        selectedMetrics={selectedMetrics}
        onlineElements={onlineElements}
        onMetricToggle={(metricKey, available) => 
          handleMetricToggle(metricKey, available, selectedMetrics, onlineElements)
        }
        onAddElement={(metricKey: string, value: string) => addOnlineElement(metricKey, value, selectedMetrics)}
        onRemoveElement={(metricKey: string, value: string) => removeOnlineElement(metricKey, value, selectedMetrics)}
      />

      <SensorCard
        sensorType="chromeleon_online"
        data={data.chromeleon_online}
        selectedMetrics={selectedMetrics}
        onlineElements={onlineElements}
        onMetricToggle={(metricKey, available) => 
          handleMetricToggle(metricKey, available, selectedMetrics, onlineElements)
        }
        onAddElement={(metricKey: string, value: string) => addOnlineElement(metricKey, value, selectedMetrics)}
        onRemoveElement={(metricKey: string, value: string) => removeOnlineElement(metricKey, value, selectedMetrics)}
      />

      <SensorCard
        sensorType="chromeleon_online_permanent_gas"
        data={data.chromeleon_online_permanent_gas}
        selectedMetrics={selectedMetrics}
        onlineElements={onlineElements}
        onMetricToggle={(metricKey, available) => 
          handleMetricToggle(metricKey, available, selectedMetrics, onlineElements)
        }
        onAddElement={(metricKey: string, value: string) => addOnlineElement(metricKey, value, selectedMetrics)}
        onRemoveElement={(metricKey: string, value: string) => removeOnlineElement(metricKey, value, selectedMetrics)}
      />

      <SensorCard
        sensorType="pignat"
        data={data.pignat}
        selectedMetrics={selectedMetrics}
        onlineElements={onlineElements}
        onMetricToggle={(metricKey, available) => 
          handleMetricToggle(metricKey, available, selectedMetrics, onlineElements)
        }
        onAddElement={(metricKey: string, value: string) => addOnlineElement(metricKey, value, selectedMetrics)}
        onRemoveElement={(metricKey: string, value: string) => removeOnlineElement(metricKey, value, selectedMetrics)}
      />

      <SensorCard
        sensorType="resume"
        data={data.resume}
        selectedMetrics={selectedMetrics}
        onlineElements={onlineElements}
        onMetricToggle={(metricKey, available) => 
          handleMetricToggle(metricKey, available, selectedMetrics, onlineElements)
        }
        onAddElement={(metricKey: string, value: string) => addOnlineElement(metricKey, value, selectedMetrics)}
        onRemoveElement={(metricKey: string, value: string) => removeOnlineElement(metricKey, value, selectedMetrics)}
      />
    </div>
  );
};

export default MetricsSelector;