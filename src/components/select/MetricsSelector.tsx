"use client";

import React from "react";
import { MetricsBySensor, SelectedMetricsBySensor, isSensorError } from "@/src/lib/utils/type";
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

  // Collect sensor errors
  const sensorErrors: Array<{ sensorName: string; message: string }> = [];
  
  if (isSensorError(data.chromeleon_offline)) {
    sensorErrors.push({ sensorName: "GC-Offline", message: data.chromeleon_offline.error });
  }
  if (isSensorError(data.chromeleon_online)) {
    sensorErrors.push({ sensorName: "GC-Online", message: data.chromeleon_online.error });
  }
  if (isSensorError(data.chromeleon_online_permanent_gas)) {
    sensorErrors.push({ sensorName: "GC-Online Permanent Gas", message: data.chromeleon_online_permanent_gas.error });
  }
  if (isSensorError(data.pignat)) {
    sensorErrors.push({ sensorName: "Pignat", message: data.pignat.error });
  }
  if (isSensorError(data.resume)) {
    sensorErrors.push({ sensorName: "Résumé", message: data.resume.error });
  }

  // Check if no data is available at all
  const hasAnyAvailableData = (
    (!isSensorError(data.chromeleon_offline) && Array.isArray(data.chromeleon_offline) && data.chromeleon_offline.length > 0) ||
    (!isSensorError(data.chromeleon_online) && Array.isArray(data.chromeleon_online) && data.chromeleon_online.length > 0) ||
    (!isSensorError(data.chromeleon_online_permanent_gas) && Array.isArray(data.chromeleon_online_permanent_gas) && data.chromeleon_online_permanent_gas.length > 0) ||
    (!isSensorError(data.pignat) && Array.isArray(data.pignat) && data.pignat.length > 0) ||
    (!isSensorError(data.resume) && Array.isArray(data.resume) && data.resume.length > 0)
  );

  return (
    <div className={`w-full max-w-2xl mx-auto space-y-4 ${className}`}>
      {/* Error messages section */}
      {sensorErrors.length > 0 && (
        <div className="mb-4 space-y-2">
          {sensorErrors.map((error, index) => (
            <div
              key={index}
              className="bg-red-50 border border-red-200 text-red-800 p-3 rounded-lg flex items-center"
            >
              <svg
                className="h-4 w-4 mr-2 flex-shrink-0"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                  clipRule="evenodd"
                />
              </svg>
              <span className="text-sm font-medium">{error.message}</span>
            </div>
          ))}
        </div>
      )}

      {/* No data available message */}
      {!hasAnyAvailableData && (
        <div className="bg-gray-50 border border-gray-200 text-gray-600 p-6 rounded-lg text-center">
          <div className="flex flex-col items-center space-y-2">
            <svg
              className="h-12 w-12 text-gray-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1}
                d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2M4 13h2m13-8V4a1 1 0 00-1-1H6a1 1 0 00-1 1v1m16 0h-2M4 5h2"
              />
            </svg>
            <div className="space-y-1">
              <h3 className="text-lg font-medium text-gray-700">Aucune donnée disponible</h3>
              <p className="text-sm text-gray-500">
                Aucune métrique n&apos;est disponible pour les fichiers uploadés. 
                Vérifiez que vos fichiers contiennent les données attendues.
              </p>
            </div>
          </div>
        </div>
      )}

      {hasAnyAvailableData && (
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
      )}
      {!isSensorError(data.chromeleon_offline) && Array.isArray(data.chromeleon_offline) && data.chromeleon_offline.length > 0 && (
        <SensorCard
          sensorType="chromeleon_offline"
          data={data.chromeleon_offline}
          selectedMetrics={selectedMetrics}
          onlineElements={onlineElements}
          onMetricToggle={handleMetricToggle}
          onAddElement={addOnlineElement}
          onRemoveElement={removeOnlineElement}
        />
      )}

      {!isSensorError(data.chromeleon_online) && Array.isArray(data.chromeleon_online) && data.chromeleon_online.length > 0 && (
        <SensorCard
          sensorType="chromeleon_online"
          data={data.chromeleon_online}
          selectedMetrics={selectedMetrics}
          onlineElements={onlineElements}
          onMetricToggle={handleMetricToggle}
          onAddElement={addOnlineElement}
          onRemoveElement={removeOnlineElement}
        />
      )}

      {!isSensorError(data.chromeleon_online_permanent_gas) && Array.isArray(data.chromeleon_online_permanent_gas) && data.chromeleon_online_permanent_gas.length > 0 && (
        <SensorCard
          sensorType="chromeleon_online_permanent_gas"
          data={data.chromeleon_online_permanent_gas}
          selectedMetrics={selectedMetrics}
          onlineElements={onlineElements}
          onMetricToggle={handleMetricToggle}
          onAddElement={addOnlineElement}
          onRemoveElement={removeOnlineElement}
        />
      )}

      {!isSensorError(data.pignat) && Array.isArray(data.pignat) && data.pignat.length > 0 && (
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
      )}

      {!isSensorError(data.resume) && Array.isArray(data.resume) && data.resume.length > 0 && (
        <SensorCard
          sensorType="resume"
          data={data.resume}
          selectedMetrics={selectedMetrics}
          onlineElements={onlineElements}
          onMetricToggle={handleMetricToggle}
          onAddElement={addOnlineElement}
          onRemoveElement={removeOnlineElement}
        />
      )}
    </div>
  );
};

export default MetricsSelector;