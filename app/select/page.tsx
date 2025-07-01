"use client";

import { getIndexByPathname, getNavigationByIndex } from "@/src/lib/pathNavigation";
import BackButton from "../components/backButton";
import NextButton from "../components/nextButton";
import { useRouter } from "next/navigation";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { getMetricsAvailable } from "@/src/lib/utils/invoke.utils";
import MetricsSelector from "./selectMetrics";
import { Metric, MetricsBySensor } from "@/src/lib/utils/type";



export default function Page() {
  const router = useRouter();
  const pathname = usePathname();

  const [metricsAvailable, setMetricsAvailable] = useState<MetricsBySensor | null>(null);

  const step = getIndexByPathname(pathname);
  const [prevPath, nextPath] = getNavigationByIndex(step);

  const handleNext = async () => {
    if (!nextPath) return;
    try {
      router.push(nextPath);
    } finally {
    }
  };

  const handleBack = async () => {
    if (!prevPath) return;
    try {
      router.push(prevPath);
    } finally {
    }
  };
  useEffect(() => {
    getMetrics();
  }, []);
  const getMetrics = async () => {
    const metricsAvailable: MetricsBySensor = await getMetricsAvailable("/home/lucaslhm/Documents");
    setMetricsAvailable(metricsAvailable);
    console.log("Metrics available:", metricsAvailable);
  }
  const handleSelectionChange = (selectedMetrics: Metric[]) => {
    console.log("Selected metrics:", selectedMetrics);
  }
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
          <NextButton onClick={handleNext} disable={!nextPath} />
        </div>
      </div>
    </div>
  );
}
