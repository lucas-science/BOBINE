"use client";

import { useState, useEffect } from "react";
import { tauriService } from "@/src/lib/services/TauriService";
import { MetricsBySensor } from "@/src/lib/utils/type";

export const useMetricsData = () => {
  const [metricsAvailable, setMetricsAvailable] = useState<MetricsBySensor | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const getMetrics = async () => {
    try {
      setLoading(true);
      setError(null);
      const docsDir = await tauriService.getDocumentsDir();
      const metrics = await tauriService.getMetricsAvailable(docsDir);
      setMetricsAvailable(metrics);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Error fetching metrics";
      console.error("Error fetching metrics:", err);
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    getMetrics();
  }, []);

  return {
    metricsAvailable,
    loading,
    error,
    refetch: getMetrics,
  };
};