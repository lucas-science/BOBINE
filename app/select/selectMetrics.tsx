"use client";

import React, { useState } from "react";
import { Card } from "@/src/components/ui/card";
import {
  MetricsBySensor,
  SelectedMetricsBySensor,
  ChromeleonOfflineMetric,
  ChromeleonOnlineMetric,
  PignaMetric,
} from "@/src/lib/utils/type";
import { MetricsSection } from "./MetricsSection";
import { MetricItem } from "./MetricItem";
import { ChromeleonOnlineItem } from "./chromeleonOnlineItem";

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
  // éléments chimiques par métrique online (clé "chromeleon_online-i")
  const [onlineElements, setOnlineElements] = useState<Record<string, string[]>>({});

  const getSensorDisplayName = (k: string) =>
    ({ chromeleon_offline: "Chromeleon Offline", chromeleon_online: "Chromeleon Online", pigna: "Pigna" } as const)[
      k as "chromeleon_offline" | "chromeleon_online" | "pigna"
    ] ?? k;

  // ---- construit SelectedMetricsBySensor à partir d’états fournis ----
  const buildSelectedFrom = (
    keys: Set<string>,
    onlineMap: Record<string, string[]>
  ): SelectedMetricsBySensor => {
    const out: SelectedMetricsBySensor = {
      chromeleon_offline: [],
      chromeleon_online: [],
      pigna: [],
    };

    keys.forEach((key) => {
      const [sensorType, indexStr] = key.split("-");
      const i = parseInt(indexStr, 10);

      if (sensorType === "chromeleon_offline") {
        const m = data.chromeleon_offline?.[i] as ChromeleonOfflineMetric | undefined;
        if (m) out.chromeleon_offline.push(m.name);
      } else if (sensorType === "pigna") {
        const m = data.pigna?.[i] as PignaMetric | undefined;
        if (m) out.pigna.push(m.name);
      } else if (sensorType === "chromeleon_online") {
        const m = data.chromeleon_online?.[i] as ChromeleonOnlineMetric | undefined;
        if (m) {
          // 👉 si la métrique n’a PAS de chimicalElements, on renvoie un tableau vide
          const hasElements = Array.isArray(m.chimicalElements) && m.chimicalElements.length > 0;
          out.chromeleon_online.push({
            name: m.name,
            chimicalElementSelected: hasElements ? (onlineMap[key] ?? []) : [],
          });
        }
      }
    });

    return out;
  };

  // ---- toggle d’une métrique ----
  const handleMetricToggle = (metricKey: string, available: boolean) => {
    if (!available) return;
    const next = new Set(selectedMetrics);
    // eslint-disable-next-line @typescript-eslint/no-unused-expressions
    next.has(metricKey) ? next.delete(metricKey) : next.add(metricKey);
    setSelectedMetrics(next);
    onSelectionChange(buildSelectedFrom(next, onlineElements));
  };

  // ---- add / remove d’un élément chimique (pour les métriques qui en ont) ----
  const addOnlineElement = (metricKey: string, value: string) => {
    const cur = new Set(onlineElements[metricKey] ?? []);
    cur.add(value);
    const nextMap = { ...onlineElements, [metricKey]: Array.from(cur) };
    setOnlineElements(nextMap);
    onSelectionChange(buildSelectedFrom(selectedMetrics, nextMap));
  };

  const removeOnlineElement = (metricKey: string, value: string) => {
    const cur = new Set(onlineElements[metricKey] ?? []);
    cur.delete(value);
    const nextMap = { ...onlineElements, [metricKey]: Array.from(cur) };
    setOnlineElements(nextMap);
    onSelectionChange(buildSelectedFrom(selectedMetrics, nextMap));
  };

  return (
    <div className={`w-full max-w-2xl mx-auto space-y-4 ${className}`}>
      {/* Chromeleon Offline */}
      <Card className="shadow-sm">
        <MetricsSection title={getSensorDisplayName("chromeleon_offline")}>
          {data.chromeleon_offline.map((metric, index) => {
            const metricKey = `chromeleon_offline-${index}`;
            const isSelected = selectedMetrics.has(metricKey);
            return (
              <MetricItem
                key={metricKey}
                metricKey={metricKey}
                name={metric.name}
                available={metric.available}
                selected={isSelected}
                onToggle={() => handleMetricToggle(metricKey, metric.available)}
              />
            );
          })}
        </MetricsSection>
      </Card>

      {/* Chromeleon Online */}
      <Card className="shadow-sm">
        <MetricsSection title={getSensorDisplayName("chromeleon_online")}>
          {data.chromeleon_online.map((metric, index) => {
            const metricKey = `chromeleon_online-${index}`;
            const isSelected = selectedMetrics.has(metricKey);
            const hasElements =
              Array.isArray(metric.chimicalElements) && metric.chimicalElements.length > 0;

            if (!hasElements) {
              // 🟦 métrique online SANS éléments chimiques -> item simple
              return (
                <MetricItem
                  key={metricKey}
                  metricKey={metricKey}
                  name={metric.name}
                  available={metric.available}
                  selected={isSelected}
                  onToggle={() => handleMetricToggle(metricKey, metric.available)}
                />
              );
            }

            // 🟨 métrique online AVEC éléments chimiques -> combobox + badges
            const chosen = onlineElements[metricKey] ?? [];
            return (
              <ChromeleonOnlineItem
                key={metricKey}
                metricKey={metricKey}
                name={metric.name}
                available={metric.available}
                selected={isSelected}
                chimicalElements={metric.chimicalElements ?? []}
                chosenElements={chosen}
                onToggle={() => handleMetricToggle(metricKey, metric.available)}
                onAddElement={(v: string) => addOnlineElement(metricKey, v)}
                onRemoveElement={(v: string) => removeOnlineElement(metricKey, v)}
              />
            );
          })}
        </MetricsSection>
      </Card>

      {/* Pigna */}
      <Card className="shadow-sm">
        <MetricsSection title={getSensorDisplayName("pigna")}>
          {data.pigna.map((metric, index) => {
            const metricKey = `pigna-${index}`;
            const isSelected = selectedMetrics.has(metricKey);
            return (
              <MetricItem
                key={metricKey}
                metricKey={metricKey}
                name={metric.name}
                available={metric.available}
                selected={isSelected}
                onToggle={() => handleMetricToggle(metricKey, metric.available)}
                subText={
                  metric.columns?.length ? `Colonnes: ${metric.columns.join(", ")}` : undefined
                }
              />
            );
          })}
        </MetricsSection>
      </Card>
    </div>
  );
};

export default MetricsSelector;
