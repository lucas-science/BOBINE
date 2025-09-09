"use client";

import { useRouter, usePathname } from "next/navigation";
import { getIndexByPathname, getNavigationByIndex } from "@/src/lib/pathNavigation";
import { SelectedMetricsBySensor } from "@/src/lib/utils/type";
import { STORAGE_KEYS } from "@/src/lib/config/constants";

export const useStepNavigation = () => {
  const router = useRouter();
  const pathname = usePathname();
  
  const step = getIndexByPathname(pathname);
  const [prevPath, nextPath] = getNavigationByIndex(step);

  const handleNext = async (selectedMetrics?: SelectedMetricsBySensor | null) => {
    if (!nextPath) return;
    try {
      if (selectedMetrics) {
        localStorage.setItem(STORAGE_KEYS.SELECTED_METRICS, JSON.stringify(selectedMetrics));
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
      localStorage.removeItem(STORAGE_KEYS.SELECTED_METRICS);
      console.log("Data removed from localStorage");
      router.push(prevPath);
    } catch (error) {
      console.error("Error navigating to previous path:", error);
    }
  };

  return {
    step,
    prevPath,
    nextPath,
    handleNext,
    handleBack,
  };
};