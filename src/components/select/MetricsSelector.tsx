"use client";

import React from "react";
import { MetricsBySensor, SelectedMetricsBySensor } from "@/src/lib/utils/type";
import { SensorCard } from "./SensorCard";
import { useMetricsSelectionWithTimeRange } from "@/src/hooks/useMetricsSelectionWithTimeRange";
import { Button } from "@/src/ui/button";

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
  const {
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
  } = useMetricsSelectionWithTimeRange(data, onSelectionChange);

  const handleToggleAll = async () => {
    if (isAllSelected()) {
      deselectAll();
    } else {
      await selectAll();
    }
  };

  return (
    <div className={`w-full max-w-2xl mx-auto space-y-4 ${className}`}>
      <div className="flex justify-center mb-6">
        <Button 
          onClick={handleToggleAll}
          variant="outline"
          size="sm"
          disabled={isLoadingTimeRange}
          className={`px-6 py-2 text-sm font-medium cursor-pointer ${
            isAllSelected() ? "bg-secondary text-white hover:bg-secondary/80 hover:text-white" : "hover:bg-secondary/20"
          }`}
        >
          {isLoadingTimeRange 
            ? "Chargement..." 
            : isAllSelected() 
              ? "Désélectionner tout" 
              : "Sélectionner tout"
          }
        </Button>
      </div>
      <SensorCard
        sensorType="chromeleon_offline"
        data={data.chromeleon_offline}
        selectedMetrics={selectedMetrics}
        onlineElements={onlineElements}
        onMetricToggle={handleMetricToggle}
        onAddElement={addOnlineElement}
        onRemoveElement={removeOnlineElement}
      />

      <SensorCard
        sensorType="chromeleon_online"
        data={data.chromeleon_online}
        selectedMetrics={selectedMetrics}
        onlineElements={onlineElements}
        onMetricToggle={handleMetricToggle}
        onAddElement={addOnlineElement}
        onRemoveElement={removeOnlineElement}
      />

      <SensorCard
        sensorType="chromeleon_online_permanent_gas"
        data={data.chromeleon_online_permanent_gas}
        selectedMetrics={selectedMetrics}
        onlineElements={onlineElements}
        onMetricToggle={handleMetricToggle}
        onAddElement={addOnlineElement}
        onRemoveElement={removeOnlineElement}
      />

      <SensorCard
        sensorType="pignat"
        data={data.pignat}
        selectedMetrics={selectedMetrics}
        onlineElements={onlineElements}
        timeRanges={timeRanges}
        timeRangeData={timeRangeData}
        isLoadingTimeRange={isLoadingTimeRange}
        onMetricToggle={handleMetricToggle}
        onTimeRangeChange={handleTimeRangeChange}
        onAddElement={addOnlineElement}
        onRemoveElement={removeOnlineElement}
      />

      <SensorCard
        sensorType="resume"
        data={data.resume}
        selectedMetrics={selectedMetrics}
        onlineElements={onlineElements}
        onMetricToggle={handleMetricToggle}
        onAddElement={addOnlineElement}
        onRemoveElement={removeOnlineElement}
      />
    </div>
  );
};

export default MetricsSelector;