import React, { useCallback, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from '@/src/components/ui/card';
import { Checkbox } from '@/src/components/ui/checkbox';
import { Metric, MetricsBySensor, SelectedMetricsBySensor } from '@/src/lib/type/type';

interface MetricsSelectorProps {
  data: MetricsBySensor;
  onSelectionChange: (selectedMetrics: SelectedMetricsBySensor) => void;
  className?: string;
}

const MetricsSelector: React.FC<MetricsSelectorProps> = ({
  data,
  onSelectionChange,
  className = ""
}) => {
  const [selectedMetrics, setSelectedMetrics] = useState<Set<string>>(new Set());

  const getSelectedMetricsBySensor = useCallback((selectedKeys: Set<string>): SelectedMetricsBySensor => {
    const result: SelectedMetricsBySensor = {
      chromeleon_offline: [],
      chromeleon_online: [],
      pigna: []
    };

    selectedKeys.forEach(key => {
      const [sensorType, indexStr] = key.split('-');
      const metricIndex = parseInt(indexStr, 10);
      const metric = data[sensorType as keyof MetricsBySensor]?.[metricIndex];

      if (metric && (sensorType === "chromeleon_offline" || sensorType === "chromeleon_online" || sensorType === "pigna")) {
        result[sensorType].push(metric.name);
      }
    });

    return result;
  }, [data]);

  const handleMetricToggle = (metricKey: string, available: boolean) => {
    if (!available) return;

    const newSelected = new Set(selectedMetrics);
    // eslint-disable-next-line @typescript-eslint/no-unused-expressions
    newSelected.has(metricKey) ? newSelected.delete(metricKey) : newSelected.add(metricKey);
    setSelectedMetrics(newSelected);
    onSelectionChange(getSelectedMetricsBySensor(newSelected));
  };

  const getSensorDisplayName = (sensorKey: string) => {
    const names = {
      chromeleon_offline: 'Chromeleon Offline',
      chromeleon_online: 'Chromeleon Online',
      pigna: 'Pigna'
    };
    if (sensorKey in names) {
      return names[sensorKey as keyof typeof names];
    }
    return sensorKey;
  };

  return (
    <div className={`w-full max-w-2xl mx-auto space-y-4 ${className}`}>
      {Object.entries(data).map(([sensorKey, metrics]) => (
        <Card key={sensorKey} className="shadow-sm">
          <CardHeader className="pb-3">
            <CardTitle className="text-lg font-semibold text-gray-900">
              {getSensorDisplayName(sensorKey)}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {metrics.map((metric: Metric, index: number) => {
              const metricKey = `${sensorKey}-${index}`;
              const isSelected = selectedMetrics.has(metricKey);

              return (
                <div
                  key={metricKey}
                  className={`flex items-start space-x-3 p-3 rounded-lg border transition-colors ${
                    metric.available
                      ? isSelected
                        ? 'bg-blue-50 border-blue-200'
                        : 'bg-white border-gray-200 hover:bg-gray-50'
                      : 'bg-gray-50 border-gray-200'
                  } ${metric.available ? 'cursor-pointer' : 'cursor-not-allowed'}`}
                  onClick={() => handleMetricToggle(metricKey, metric.available)}
                >
                  <Checkbox
                    checked={isSelected}
                    disabled={!metric.available}
                    className={`mt-0.5 ${!metric.available ? 'opacity-50' : ''}`}
                    onCheckedChange={() => handleMetricToggle(metricKey, metric.available)}
                  />
                  <div className="flex-1 min-w-0">
                    <p className={`text-sm leading-5 ${metric.available ? 'text-gray-900' : 'text-gray-400'}`}>
                      {metric.name}
                    </p>
                    <p className={`text-xs mt-1 ${metric.available ? 'text-gray-500' : 'text-gray-300'}`}>
                      Colonnes: {metric.columns.length > 0 ? metric.columns.join(', ') : metric.columns}
                    </p>
                  </div>
                </div>
              );
            })}
          </CardContent>
        </Card>
      ))}
    </div>
  );
};

export default MetricsSelector;
