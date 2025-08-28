"use client";

import { getIndexByPathname, getNavigationByIndex } from "@/src/lib/pathNavigation";
import BackButton from "../components/backButton";
import NextButton from "../components/nextButton";
import { useRouter } from "next/navigation";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { getMetricsAvailable } from "@/src/lib/utils/invoke.utils";
import MetricsSelector from "./selectMetrics";
import { MetricsBySensor, SelectedMetricsBySensor } from "@/src/lib/utils/type";
import { invoke } from "@tauri-apps/api/core";
import { info } from '@tauri-apps/plugin-log';

export default function Page() {
  const router = useRouter();
  const pathname = usePathname();

  const [metricsAvailable, setMetricsAvailable] = useState<MetricsBySensor | null>(null);
  const [selectedMetrics, setSelectedMetrics] = useState<SelectedMetricsBySensor | null>(null);

  const step = getIndexByPathname(pathname);
  const [prevPath, nextPath] = getNavigationByIndex(step);

  const handleNext = async () => {
    if (!nextPath) return;
    try {
      if (selectedMetrics) {
        localStorage.setItem('selectedMetrics', JSON.stringify(selectedMetrics));
        console.log("Metrics saved to localStorage:", selectedMetrics);
      }
      router.push(nextPath);
    } catch (error) {
      console.error("Error navigating to next path:", error);
    }
  };

  const handleBack = async () => {
    if (!prevPath) return;
    try {
      localStorage.removeItem('selectedMetrics');
      console.log("Data removed from localStorage");
      router.push(prevPath);
    } catch (error) {
      console.error("Error navigating to previous path:", error);
    }
  };

  const getMetrics = async () => {
    try {
      const docsDir: string = await invoke("get_documents_dir");
      const metrics = await getMetricsAvailable(docsDir); // ← plus de parse stdout
      info("Metrics fetched:" + JSON.stringify(metrics));
      setMetricsAvailable(metrics);
    } catch (error) {
      console.error("Error fetching metrics:", error);
    }
  };


  const handleSelectionChange = (selectedMetrics: SelectedMetricsBySensor) => {
    console.log("Selected metrics:", selectedMetrics);
    setSelectedMetrics(selectedMetrics);
  };

  useEffect(() => {
    getMetrics();
  }, []);

  const hasSelectedMetrics = selectedMetrics && Object.values(selectedMetrics).some(arr => arr.length > 0);

  return (
    <div>
      {metricsAvailable && (
        <MetricsSelector
          data={metricsAvailable}
          onSelectionChange={handleSelectionChange}
        />
      )}
      <div className="fixed bottom-0 left-0 right-0 bg-amber-300 p-4">
        <div className="flex justify-between items-center w-full mx-auto">
          <BackButton onClick={handleBack} disable={!prevPath} />
          <NextButton
            onClick={handleNext}
            disable={!nextPath || !hasSelectedMetrics}
          />
        </div>
      </div>
    </div>
  );
}
